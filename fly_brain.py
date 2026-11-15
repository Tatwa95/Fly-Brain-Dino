"""
Spiking network with one unit per fruit-fly neuron (default 166,700, the size of
the Janelia / Google Research male CNS connectome, "MaleCNS v1.0").

* Every neuron is a leaky integrate-and-fire unit and all of them are simulated.
* The game state is written into ~12k "sensory" neurons with population coding
  (each neuron has a preferred value, like a real tuning curve).
* Spikes travel through the synapses (sparse wiring, ~2.7 M synapses by default,
  or your own real connectome via --connectome).
* The action is read out from ALL neurons: a plastic readout (one weight per
  neuron and action) is trained with a dopamine-like teaching signal.
"""
import os
import time
import numpy as np

N_NEURONS_DEFAULT = 166_700

                                                                            
CHANNELS = [
    ("distance", (0.13, 0.28, 0.31, 0.80), "time until obstacle arrives"),
    ("height",   (0.69, 0.28, 0.87, 0.80), "obstacle height"),
    ("width",    (0.32, 0.10, 0.49, 0.36), "obstacle width"),
    ("speed",    (0.51, 0.10, 0.68, 0.36), "game speed"),
    ("clear",    (0.33, 0.38, 0.44, 0.50), "time until obstacle has passed"),
    ("behind",   (0.56, 0.38, 0.67, 0.50), "obstacle behind us"),
    ("dino_y",   (0.33, 0.52, 0.47, 0.75), "dino altitude"),
    ("dino_vy",  (0.53, 0.52, 0.67, 0.75), "dino velocity"),
    ("duck",     (0.42, 0.76, 0.58, 0.93), "ducking?"),
    ("bird",     (0.70, 0.76, 0.86, 0.93), "pterodactyl present?"),
]

ROLE_INTER, ROLE_SENSE, ROLE_JUMP, ROLE_DUCK = 0, 1, 2, 3


class FlyBrain:
    def __init__(self, positions, panel_size, n_per_channel=1500, out_degree=16,
                 seed=7, connectome=None, log=print):
        self.rng = np.random.default_rng(seed)
        self.pos = positions
        self.N = len(positions)
        pw, ph = panel_size
        self.panel = (pw, ph)
        self.log = log

                                                                                 
        t0 = time.time()
        if connectome and os.path.exists(connectome):
            self._load_connectome(connectome)
            self.wiring_source = f"real connectome file ({os.path.basename(connectome)})"
        else:
            self._build_synthetic(out_degree)
            self.wiring_source = "synthetic connectome-like wiring (spatially local + long range)"
        self.n_syn = int(self.indices.size)
        log(f"  wiring: {self.N:,} neurons, {self.n_syn:,} synapses  ({time.time()-t0:.1f}s)")

                                                                                 
        self.v = np.zeros(self.N, np.float32)
        self.syn = np.zeros(self.N, np.float32)
        self.rate = np.zeros(self.N, np.float32)
        self.leak_v = 0.90
        self.leak_s = 0.60
        self.leak_r = 0.72
        self.noise = 0.13
        self.spk = np.zeros(0, np.int64)
        self.thr = 1.0

                                                                                 
        self._assign_sensory(n_per_channel)

                                                                                
        self.W = np.zeros((2, self.N), np.float32)                                 
        self.b = np.zeros(2, np.float32)
        self.role = np.zeros(self.N, np.uint8)
        self.role[self.s_idx] = ROLE_SENSE
        self.lr = 0.35
        self.out = np.zeros(2, np.float32)
        self.trained_steps = 0
        self.total_spikes_last = 0

                                                                               
    def _build_synthetic(self, K):
        N = self.N
        pw, ph = self.panel
        rng = self.rng
        px, py = self.pos[:, 0], self.pos[:, 1]
        owner = np.full(pw * ph, -1, np.int32)
        owner[py * pw + px] = np.arange(N, dtype=np.int32)
        tgt = np.empty((N, K), np.int32)
        sigma = 20.0
        for c0 in range(0, N, 25_000):
            c1 = min(N, c0 + 25_000)
            n = c1 - c0
            tx = np.clip(px[c0:c1, None] + rng.normal(0, sigma, (n, K)).astype(np.int32), 0, pw - 1)
            ty = np.clip(py[c0:c1, None] + rng.normal(0, sigma, (n, K)).astype(np.int32), 0, ph - 1)
            t = owner[ty * pw + tx]
            bad = (t < 0) | (rng.random((n, K)) < 0.07)                                
            t[bad] = rng.integers(0, N, bad.sum(), dtype=np.int32)
            tgt[c0:c1] = t
        selfhit = tgt == np.arange(N, dtype=np.int32)[:, None]
        tgt[selfhit] = rng.integers(0, N, selfhit.sum(), dtype=np.int32)
        exc = rng.random(N) < 0.8
        base = 0.128
        mag = (0.6 + 0.8 * rng.random((N, K))).astype(np.float32) * base
        w = np.where(exc[:, None], mag, -mag * 12.5).astype(np.float32)
        self.exc = exc
        self.indptr = np.arange(N + 1, dtype=np.int64) * K
        self.indices = tgt.ravel()
        self.data = w.ravel()

    def _load_connectome(self, path):
        """.npz with arrays pre, post, weight (and optional sign) -> CSC-like arrays."""
        d = np.load(path)
        pre, post, wt = d["pre"], d["post"], d["weight"].astype(np.float32)
        ids, inv = np.unique(np.concatenate([pre, post]), return_inverse=True)
        n_all = len(ids)
        pre_i, post_i = inv[: len(pre)], inv[len(pre):]
        if n_all != self.N:
            self.log(f"  connectome has {n_all:,} neurons; using that number")
            raise SystemExit(f"Connectome has {n_all} neurons but the view was built for {self.N}. "
                             f"Start with --neurons {n_all}")
        sign = d["sign"].astype(np.float32) if "sign" in d.files else None
        if sign is None:
            self.exc = self.rng.random(self.N) < 0.8
            sign = np.where(self.exc[pre_i], 1.0, -12.5).astype(np.float32)
        else:
            self.exc = np.ones(self.N, bool)
        wt = wt * sign
        strength = np.bincount(post_i, weights=np.abs(wt), minlength=self.N).astype(np.float32)
        wt = wt / np.maximum(strength[post_i], 1.0) * 16 * 0.128
        order = np.argsort(pre_i, kind="stable")
        self.indices = post_i[order].astype(np.int32)
        self.data = wt[order].astype(np.float32)
        cnt = np.bincount(pre_i, minlength=self.N)
        self.indptr = np.concatenate([[0], np.cumsum(cnt)]).astype(np.int64)

                                                                              
    def _assign_sensory(self, n_per):
        pw, ph = self.panel
        fx = self.pos[:, 0] / pw
        fy = self.pos[:, 1] / ph
        used = np.zeros(self.N, bool)
        s_idx, s_ch, s_pref = [], [], []
        self.channel_names = [c[0] for c in CHANNELS]
        self.channel_regions = {}
        for ci, (name, (x0, y0, x1, y1), _) in enumerate(CHANNELS):
            cand = np.flatnonzero((fx >= x0) & (fx <= x1) & (fy >= y0) & (fy <= y1) & ~used)
            if len(cand) == 0:
                cand = np.flatnonzero(~used)
            take = self.rng.choice(cand, size=min(n_per, len(cand)), replace=False)
            used[take] = True
            s_idx.append(take)
            s_ch.append(np.full(len(take), ci, np.int8))
                                                      
            s_pref.append(self.rng.permutation(np.linspace(0.0, 1.0, len(take), dtype=np.float32)))
            self.channel_regions[name] = (x0, y0, x1, y1)
        self.s_idx = np.concatenate(s_idx).astype(np.int64)
        self.s_ch = np.concatenate(s_ch)
        self.s_pref = np.concatenate(s_pref)
        self.sigma = 0.045
        self.gain = 0.7

    def encode(self, feats):
        """feats: dict name -> value in 0..1 (missing = channel silent)."""
        vals = np.full(len(CHANNELS), np.nan, np.float32)
        for i, name in enumerate(self.channel_names):
            if name in feats:
                vals[i] = feats[name]
        x = vals[self.s_ch]
        with np.errstate(invalid="ignore"):
            a = np.exp(-0.5 * ((x - self.s_pref) / self.sigma) ** 2)
        a = np.nan_to_num(a, nan=0.0)
        m = a > 0.08
        return self.s_idx[m], (self.gain * a[m]).astype(np.float32)

                                                                                 
    def _substep(self, ext_idx, ext_val):
        N = self.N
        idx = self.spk
        self.syn *= self.leak_s
        if idx.size:
            starts = self.indptr[idx]
            cnt = self.indptr[idx + 1] - starts
            tot = int(cnt.sum())
            if tot:
                offs = np.repeat(starts - (np.cumsum(cnt) - cnt), cnt) + np.arange(tot)
                inp = np.bincount(self.indices[offs], weights=self.data[offs], minlength=N)
                self.syn += inp.astype(np.float32)
        self.v *= self.leak_v
        self.v += self.syn
        self.v += self.rng.standard_normal(N, dtype=np.float32) * self.noise
        if ext_idx.size:
            self.v[ext_idx] += ext_val
        spk = np.flatnonzero(self.v > self.thr)
        frac = spk.size / N
        if frac > 0.04:                                                                           
            self.v -= (frac - 0.04) * 8.0
        self.v[spk] = 0.0
        self.rate *= self.leak_r
        self.rate[spk] += 1.0 - self.leak_r
        self.spk = spk
        return spk

    def tick(self, feats, substeps=2):
        ext_idx, ext_val = self.encode(feats)
        out = []
        for _ in range(substeps):
            out.append(self._substep(ext_idx, ext_val))
        self.total_spikes_last = int(sum(len(s) for s in out))
        return out

                                                                                
    def read(self):
        self.out = self.W @ self.rate + self.b
        return self.out

    def train(self, target, lr=None, rate=None):
        """normalised-LMS delta rule on the plastic readout synapses (dopamine-like
        teaching signal `target` = what the coach wanted)."""
        lr = self.lr if lr is None else lr
        r = self.rate if rate is None else rate
        y = self.W @ r + self.b
        err = (np.asarray(target, np.float32) - y)
        norm = float(r @ r) + 1.0
        self.W += (lr * err / norm)[:, None] * r[None, :]
        self.b += 0.02 * err
        self.trained_steps += 1
        return err

    def update_roles(self, k=2500):
        """neurons that push hardest towards JUMP / DUCK (for the visualisation)."""
        role = np.zeros(self.N, np.uint8)
        role[self.s_idx] = ROLE_SENSE
        for row, r in ((0, ROLE_JUMP), (1, ROLE_DUCK)):
            w = self.W[row].copy()
            w[self.s_idx] = -np.inf
            top = np.argpartition(-w, k)[:k]
            top = top[w[top] > 0]
            role[top] = r
        self.role = role

                                                                               
    def save(self, path):
                                                                                    
        np.savez_compressed(path, W=self.W, b=self.b, n=self.N, version=2)

    def load(self, path):
        d = np.load(path)
        if int(d["n"]) == self.N and int(d.get("version", 1)) == 2:
            self.W = d["W"].astype(np.float32)
            self.b = d["b"].astype(np.float32)
            return True
        return False
