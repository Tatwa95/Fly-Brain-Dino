"""
FLY-BRAIN DINO
==============
Chrome's dinosaur game played by a simulated fruit-fly brain (166,700 neurons).

    python main.py
    python main.py --substeps 1
    python main.py --connectome my_connectome.npz

Keys
    1  human plays (SPACE / UP = jump, DOWN = duck)  - the fly brain just watches
    2  LEARN: coach plays, the fly brain learns by watching (dopamine-like signal)
    3  FLY BRAIN plays
    P  plasticity on/off while the brain plays      B  birds on/off
    F  fast-forward x4                              R  restart game
    S  save the trained synapses                    ESC quit
"""
import argparse
import collections
import os
import sys
import time

import numpy as np
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from brain_view import BrainView, ROLE_COLORS                      
from fly_brain import FlyBrain, CHANNELS, N_NEURONS_DEFAULT               
import dino_game as dg                                               

WIN_W, WIN_H = 1280, 760
GAME_POS = (40, 10)
BRAIN_POS = (20, 322)
BRAIN_SIZE = (760, 428)
INFO_X = 800

BG = (16, 17, 24)
PANEL = (24, 26, 36)
TXT = (222, 226, 236)
DIM = (130, 136, 152)
CYAN = (70, 220, 255)
GREEN = (90, 255, 130)
ORANGE = (255, 150, 50)
RED = (255, 90, 90)


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--neurons", type=int, default=N_NEURONS_DEFAULT)
    ap.add_argument("--connectome", default=None, help=".npz with pre, post, weight [, sign]")
    ap.add_argument("--substeps", type=int, default=2, help="brain simulation steps per game frame")
    ap.add_argument("--visual-fps", type=int, default=30,
                    help="brain-panel refresh rate (0 = every display frame)")
    ap.add_argument("--weights", default=os.path.join(HERE, "brain_weights.npz"))
    ap.add_argument("--image", default=os.path.join(HERE, "assets", "brain.webp"))
    ap.add_argument("--no-birds", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    return ap.parse_args()


def font(size, bold=True):
    return pygame.font.SysFont("consolas,dejavusansmono,couriernew,monospace", size, bold=bold)


def draw_text(surf, txt, pos, f, col=TXT):
    surf.blit(f.render(txt, True, col), pos)


def bar(surf, x, y, w, h, value, label, color, f):
    pygame.draw.rect(surf, (40, 43, 58), (x, y, w, h), border_radius=3)
    v = max(0.0, min(1.0, float(value)))
    pygame.draw.rect(surf, color, (x, y, int(w * v), h), border_radius=3)
    pygame.draw.line(surf, (255, 255, 255), (x + w // 2, y - 2), (x + w // 2, y + h + 2), 1)                    
    draw_text(surf, label, (x + 6, y + 1), f, (10, 10, 14) if v > 0.25 else TXT)


def main():
    args = parse()
    pygame.init()
    pygame.display.set_caption("Fly-Brain Dino  -  a fruit fly connectome plays the Chrome dinosaur game")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()
    f_small, f_med, f_big, f_score = font(13), font(15), font(20), font(26)

    def splash(msg):
        screen.fill(BG)
        draw_text(screen, "FLY-BRAIN DINO", (WIN_W // 2 - 120, WIN_H // 2 - 50), f_big, CYAN)
        draw_text(screen, msg, (WIN_W // 2 - 260, WIN_H // 2), f_med, TXT)
        pygame.display.flip()
        pygame.event.pump()

    splash(f"placing {args.neurons:,} neurons on the brain image ...")
    view = BrainView(args.image, BRAIN_SIZE, args.neurons)
    splash("wiring the synapses ...")
    brain = FlyBrain(view.pos, BRAIN_SIZE, connectome=args.connectome, log=lambda *a: None)
    game = dg.Game(birds=not args.no_birds, seed=args.seed)
    surf_game = pygame.Surface((dg.W, dg.H))

    mode = "learn"
    loaded = brain.load(args.weights) if os.path.exists(args.weights) else False
    if loaded:
        mode = "brain"
        brain.update_roles()
    plasticity = True
    turbo = 1
    msg, msg_t = ("saved synapses loaded - the fly brain takes over" if loaded else
                  "LEARN mode: the fly brain watches the coach and adjusts its synapses"), 240

    agree = collections.deque(maxlen=600)
    replay = collections.deque(maxlen=30)
    spark = collections.deque([0] * 240, maxlen=240)
    deaths, best_life, cur_life = 0, 0.0, 0
    feats, spikes = {}, []
    fps_hist = 60.0
    frame = 0
    brain_frame = None
    next_brain_render = 0

    running = True
    while running:
        jump_key = duck_key = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k == pygame.K_1:
                    mode, msg, msg_t = "human", "HUMAN mode: SPACE / UP jump, DOWN duck", 200
                elif k == pygame.K_2:
                    mode, msg, msg_t = "learn", "LEARN mode: the coach drives, the brain learns", 200
                elif k == pygame.K_3:
                    mode, msg, msg_t = "brain", "FLY BRAIN is driving", 200
                    brain.update_roles()
                elif k == pygame.K_p:
                    plasticity = not plasticity
                    msg, msg_t = f"plasticity {'ON' if plasticity else 'OFF'}", 120
                elif k == pygame.K_b:
                    game.birds_enabled = not game.birds_enabled
                    msg, msg_t = f"birds {'ON' if game.birds_enabled else 'OFF'}", 120
                elif k == pygame.K_f:
                    turbo = 4 if turbo == 1 else 1
                    msg, msg_t = f"fast-forward x{turbo}", 120
                elif k == pygame.K_r:
                    game.reset()
                elif k == pygame.K_s:
                    brain.save(args.weights)
                    msg, msg_t = "synapses saved to brain_weights.npz", 150
                elif k in (pygame.K_SPACE, pygame.K_UP) and game.crashed and mode == "human":
                    game.reset()
        keys = pygame.key.get_pressed()
        jump_key = keys[pygame.K_SPACE] or keys[pygame.K_UP]
        duck_key = keys[pygame.K_DOWN]

        for _ in range(turbo):
                                                                                        
            feats = game.features()
            spikes = brain.tick(feats, args.substeps)
            out = brain.read()
            jl, dl = game.coach()
            pj, pd = bool(out[0] > 0.5), bool(out[1] > 0.5)
            if not game.crashed:
                spark.append(brain.total_spikes_last)
                if mode != "human":
                    active = game.next_obstacle() is not None or game.jumping
                    if active:
                        agree.append(1 if (pj == bool(jl) and pd == bool(dl)) else 0)

                                                                              
            if mode == "human":
                a = (jump_key, duck_key)
            elif mode == "learn":
                a = (bool(jl), bool(dl))
            else:
                a = (pj, pd)

                                                                                
            if not game.crashed:
                if mode == "learn":
                    brain.train([jl, dl])
                elif mode == "brain" and plasticity:
                    brain.train([jl, dl], lr=0.1)
                if mode != "human":
                    replay.append((brain.rate.copy(), (jl, dl)))

            alive = game.step(*a)
            cur_life += 1
            if not alive and game.crash_timer == 1:
                deaths += 1
                best_life = max(best_life, game.score)
                cur_life = 0
                if mode == "brain" and plasticity:                                                  
                    for _ in range(2):
                        for r, lab in replay:
                            brain.train(list(lab), lr=0.3, rate=r)
                replay.clear()
                                                                               
                                                     
            if game.crashed and mode != "human" and game.crash_timer > 110:
                game.reset()

                                                                                    
            if mode == "learn" and len(agree) >= 600 and brain.trained_steps >= 1500 \
                    and np.mean(agree) >= 0.94:
                mode = "brain"
                brain.update_roles()
                msg, msg_t = "agreement >= 94%  ->  the FLY BRAIN takes the controls!", 300
        frame += 1
        if frame % 60 == 0 and brain.trained_steps:
            brain.update_roles()

                                                                               
        screen.fill(BG)
        game.draw(surf_game, show_score=False)
        screen.blit(pygame.transform.scale(surf_game, (dg.W * 2, dg.H * 2)), GAME_POS)
        if not (game.flash and (game.flash // 6) % 2 == 0):
            score_col = (188, 192, 202) if game.night else (92, 96, 106)
            score = f_score.render(f"{int(game.score):05d}", True, score_col)
            score_x = GAME_POS[0] + dg.W * 2 - 18 - score.get_width()
            screen.blit(score, (score_x, GAME_POS[1] + 12))
            if game.hi > 0:
                best = f_med.render(f"HI {int(game.hi):05d}", True, score_col)
                screen.blit(best, (score_x - best.get_width() - 18, GAME_POS[1] + 19))

                                                                               
                                                                            
                                                     
        now = pygame.time.get_ticks()
        visual_interval = 0 if args.visual_fps <= 0 else max(1, 1000 // args.visual_fps)
        if brain_frame is None or now >= next_brain_render:
            title = (f"Drosophila male CNS  |  {brain.N:,} neurons  |  "
                     f"{brain.total_spikes_last // max(1, args.substeps):,} firing now")
            brain_frame = view.render(spikes, brain.role, brain.channel_regions, feats, title)
            next_brain_render = now + visual_interval
        screen.blit(brain_frame, BRAIN_POS)
        pygame.draw.rect(screen, (60, 64, 84), (*BRAIN_POS, *BRAIN_SIZE), 1)

                    
        px, py = INFO_X, 322
        pygame.draw.rect(screen, PANEL, (px, py, WIN_W - px - 20, 428), border_radius=6)
        x = px + 14
        y = py + 10
        mode_col = {"human": ORANGE, "learn": CYAN, "brain": GREEN}[mode]
        mode_txt = {"human": "HUMAN PLAYS", "learn": "LEARNING (coach drives)", "brain": "FLY BRAIN PLAYS"}[mode]
        draw_text(screen, mode_txt, (x, y), f_big, mode_col)
        y += 30
        fps_hist = fps_hist * 0.90 + clock.get_fps() * 0.10
        draw_text(screen, f"neurons {brain.N:,}   synapses {brain.n_syn:,}", (x, y), f_small, DIM); y += 17
        draw_text(screen, f"FPS {fps_hist:4.0f}   sim steps/frame {args.substeps}   x{turbo}", (x, y), f_small, DIM); y += 22

        draw_text(screen, "readout of ALL neurons  (white line = key press)", (x, y), f_small, TXT); y += 18
        bar(screen, x, y, 430, 18, out[0], f"JUMP  {out[0]:+.2f}", GREEN, f_small); y += 24
        bar(screen, x, y, 430, 18, out[1], f"DUCK  {out[1]:+.2f}", ORANGE, f_small); y += 30

        ag = np.mean(agree) if len(agree) else 0.0
        draw_text(screen, f"score {int(game.score):5d}   best {int(max(best_life, game.hi)):5d}   crashes {deaths}", (x, y), f_med, TXT); y += 22
        draw_text(screen, f"agreement with coach {ag*100:5.1f}%   plasticity {'ON' if plasticity else 'off'}", (x, y), f_small, DIM); y += 24

        obstacle = game.next_obstacle()
        if obstacle is None:
            obstacle_txt, obstacle_col = "next obstacle: scanning horizon", DIM
        elif obstacle.kind == "bird" and obstacle.bottom < 80:
            obstacle_txt, obstacle_col = "next obstacle: LOW BIRD  →  DUCK", ORANGE
        elif obstacle.kind == "bird":
            obstacle_txt, obstacle_col = "next obstacle: high bird  →  hold course", CYAN
        else:
            obstacle_txt, obstacle_col = "next obstacle: cactus  →  JUMP", GREEN
        draw_text(screen, obstacle_txt, (x, y), f_small, obstacle_col); y += 23

                                     
        draw_text(screen, "neurons firing per frame", (x, y), f_small, TXT); y += 16
        sh, sw = 46, 430
        pygame.draw.rect(screen, (14, 15, 22), (x, y, sw, sh))
        arr = np.array(spark, dtype=np.float32)
        top = max(1.0, arr.max())
        pts = [(float(x + i * sw / (len(arr) - 1)), float(y + sh - 2 - (v / top) * (sh - 4))) for i, v in enumerate(arr)]
        pygame.draw.lines(screen, CYAN, False, pts, 1)
        y += sh + 10

                
        draw_text(screen, "brain colours", (x, y), f_small, TXT); y += 17
        names = ["interneuron", "sensory input", "jump neurons", "duck neurons"]
        for i, n in enumerate(names):
            c = tuple(int(v) for v in ROLE_COLORS[i])
            cx = x + (i % 2) * 215
            cy = y + (i // 2) * 17
            pygame.draw.circle(screen, c, (cx + 6, cy + 7), 5)
            draw_text(screen, n, (cx + 18, cy), f_small, DIM)
        y += 40
        pygame.draw.line(screen, (54, 58, 76), (x, y - 5), (x + 430, y - 5))
        draw_text(screen, "1 human  2 learn  3 fly brain   P plasticity", (x, y), f_small, DIM); y += 16
        draw_text(screen, "B birds   F fast x4   R restart   S save   ESC", (x, y), f_small, DIM); y += 20
        if msg_t > 0:
            draw_text(screen, msg, (x, y), f_small, mode_col)
            msg_t -= 1

        pygame.display.flip()
        clock.tick(60)

    try:
        brain.save(args.weights)
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    main()
