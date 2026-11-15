"""Brain panel: the uploaded fruit-fly brain image with every neuron placed on it.
Neurons that spike light up (colour = role) on top of the dimmed picture."""
import numpy as np
import pygame

try:
    from PIL import Image
except ImportError:                            
    Image = None

ROLE_COLORS = np.array([
    [255, 214, 120],                               
    [70, 220, 255],                          
    [90, 255, 130],                          
    [255, 130, 40],                           
], np.float32)


ROLE_GAIN = [0.42, 1.0, 1.0, 1.0]                                                              


def load_image(path, size):
    w, h = size
    if Image is not None:
        im = Image.open(path).convert("RGB")
        im = im.resize((w, h), Image.LANCZOS)
        return np.asarray(im, dtype=np.uint8)
    surf = pygame.image.load(path)
    surf = pygame.transform.smoothscale(surf, (w, h))
    return np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)).copy()


class BrainView:
    def __init__(self, image_path, size, n_neurons, seed=7):
        self.w, self.h = size
        rng = np.random.default_rng(seed)
        img = load_image(image_path, size)                                  
        mx, mn = img.max(axis=2).astype(int), img.min(axis=2).astype(int)
        mask = (mn < 236) | ((mx - mn) > 22)
        ys, xs = np.nonzero(mask)
        pick = rng.integers(0, len(xs), n_neurons)
        self.pos = np.stack([xs[pick], ys[pick]], axis=1).astype(np.int64)                  
        self.pix = (self.pos[:, 1] * self.w + self.pos[:, 0]).astype(np.int64)
        self.n = n_neurons
                                
        bg = np.zeros((self.h, self.w, 3), np.float32)
        bg[:] = (9, 10, 16)
        bg[mask] = img[mask].astype(np.float32) * 0.30 + np.array([6, 6, 10], np.float32)
        self.bg = bg
        P = self.h * self.w
        self.P = P
        self.col = np.zeros((P, 3), np.float32)
        self.bg_flat = bg.reshape(P, 3).copy()
        self.role_col = (ROLE_COLORS * np.array(ROLE_GAIN, np.float32)[:, None] * 0.9).astype(np.float32)
        self.surface = pygame.Surface((self.w, self.h))
        self.font = pygame.font.SysFont("consolas,dejavusansmono,couriernew,monospace", 12, bold=True)
        self.font_title = pygame.font.SysFont("consolas,dejavusansmono,couriernew,monospace", 14, bold=True)

    def render(self, spike_lists, role, channel_regions, chan_values, title):
        P, W = self.P, self.w
        col = self.col
        col *= 0.55                                                    
        for spk in spike_lists:
            if len(spk) == 0:
                continue
            c = self.role_col[role[spk]]
            p = self.pix[spk]
            col[p] += c                                                  
            col[np.minimum(p + 1, P - 1)] += c * 0.3                                      
            col[np.minimum(p + W, P - 1)] += c * 0.3
        img = np.minimum(self.bg_flat + col, 255.0).astype(np.uint8)
        tmp = pygame.image.frombuffer(img, (self.w, self.h), "RGB")
        self.surface.blit(tmp, (0, 0))
                                      
        s = self.surface
        for name, (x0, y0, x1, y1) in channel_regions.items():
            v = chan_values.get(name)
            cx, cy = int((x0 + x1) / 2 * self.w), int(y0 * self.h)
            col = (70, 220, 255) if v is not None else (90, 110, 120)
            t = self.font.render(name.upper(), True, col)
            pygame.draw.rect(s, (0, 0, 0), (cx - t.get_width() // 2 - 2, cy - 1, t.get_width() + 4, t.get_height()))
            s.blit(t, (cx - t.get_width() // 2, cy - 1))
        s.blit(self.font_title.render(title, True, (225, 230, 240)), (8, 6))
        return s
