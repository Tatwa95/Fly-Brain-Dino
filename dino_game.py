"""
Chrome "T-Rex runner" clone (600x150 logical canvas, drawn 2x like the real thing).

The physics constants follow the original Chromium source (gravity 0.6, initial
jump velocity -10 - speed/10, speed 6 -> 13, acceleration 0.001, obstacle gap
formula, score = distance * 0.025 ...).
"""
import os
import random
import pygame

W, H = 600, 150
GROUND_Y = 139                                   
FEET_Y = 140                                                 
DINO_X = 50

GRAVITY = 0.6
INIT_JUMP_V = -10.0
DROP_COEFF = 3.0
START_SPEED = 6.0
MAX_SPEED = 13.0
ACCEL = 0.001
SCORE_COEFF = 0.025

DAY = {"bg": (247, 247, 247), "fg": (83, 83, 83), "cloud": (220, 220, 220)}
NIGHT = {"bg": (32, 33, 36), "fg": (172, 172, 172), "cloud": (70, 70, 74)}
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

                                                                               
                                                                            
                               
DINO_UPPER = [
    "...........#########..",
    "..........###########.",
    "..........##.#########",
    "..........############",
    "..........############",
    "..........############",
    "..........#####.......",
    "..........########...",
    "#.........########...",
    "#.......###########..",
    "#......#############.",
    "##.....#############.",
    "###...##############.",
    "####..##############.",
    ".####################",
    ".###################.",
    "..###########.......",
]
DINO_UPPER = [r.ljust(22, ".")[:22] for r in DINO_UPPER]

               
LEGS_STAND = [
    "...######..#####.....",
    "....####....####.....",
    "....###.....###......",
    "....###.....###......",
    "....###.....###......",
    "....####....####.....",
    ".....###.....###.....",
]
LEGS_A = [                               
    "...######..#####.....",
    "....####...####......",
    "....###....###.......",
    "....###...####.......",
    "....####..............",
    ".....###..............",
    "......................",
]
LEGS_B = [                               
    "...######..#####.....",
    "....####....####.....",
    "....###.....###......",
    "....####....###......",
    ".............####....",
    "..............###....",
    "......................",
]
LEGS_A = [r.ljust(22, ".")[:22] for r in LEGS_A]
LEGS_B = [r.ljust(22, ".")[:22] for r in LEGS_B]
LEGS_STAND = [r.ljust(22, ".")[:22] for r in LEGS_STAND]

DINO_DUCK_A = [
    "...............#########",
    "..............###########",
    "..............##.#########",
    "..............############",
    "#.............######......",
    "##.....##############.....",
    "###...#############.#.....",
    "########################..",
    ".######################...",
    "..#####################...",
    "...##########.#.#####.....",
    "....####..###....###......",
    "....###...###.....##......",
]
DINO_DUCK_B = [
    "...............#########",
    "..............###########",
    "..............##.#########",
    "..............############",
    "#.............######......",
    "##.....##############.....",
    "###...#############.#.....",
    "########################..",
    ".######################...",
    "..#####################...",
    "...##########.#.#####.....",
    "....###...####...###......",
    "....##....###....###......",
]
DINO_DUCK_A = [r.ljust(26, ".")[:26] for r in DINO_DUCK_A]
DINO_DUCK_B = [r.ljust(26, ".")[:26] for r in DINO_DUCK_B]

BIRD_UP = [
    "...............#..........",
    "..............##..........",
    ".............###..........",
    "............####..........",
    "...........#####..........",
    "......##...######.........",
    "...#######.########.......",
    "##############.###########.",
    "...#################......",
    ".....##############.......",
    ".......##########.........",
    ".........####.............",
]
BIRD_DOWN = [
    "..........................",
    "..........................",
    "...........##.............",
    "......##..#####...........",
    "...#######.#######........",
    "##############.###########",
    "...#################......",
    ".....###############......",
    ".......###.###########....",
    "......###........####.....",
    ".....###..................",
    "....###...................",
]
BIRD_UP = [r.ljust(26, ".")[:26] for r in BIRD_UP]
BIRD_DOWN = [r.ljust(26, ".")[:26] for r in BIRD_DOWN]


def art_surface(rows, color, scale=2):
    h, w = len(rows), max(len(r) for r in rows)
    s = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                s.fill(color, (x * scale, y * scale, scale, scale))
    return s


def reference_sprite(filename, size, color):
    """Recolour a transparent, user-supplied sprite for the current palette."""
    raw = pygame.image.load(os.path.join(ASSET_DIR, filename)).convert_alpha()
    mask = pygame.mask.from_surface(raw, threshold=20)
    solid = mask.to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    return pygame.transform.scale(solid, size)


def cactus_group(sprite, count):
    """Build a compact group from the supplied cactus instead of generic shapes."""
    w, h = sprite.get_size()
    group = pygame.Surface((w + (count - 1) * (w - 5), h), pygame.SRCALPHA)
    for i in range(count):
        group.blit(sprite, (i * (w - 5), 0))
    return group


def dead_sprite(sprite, color):
    """Keep the supplied dino silhouette, with an unmistakable crash marker."""
    out = sprite.copy()
    x, y = int(sprite.get_width() * 0.72), int(sprite.get_height() * 0.18)
    mark = (235, 75, 75) if sum(color) < 400 else (150, 35, 35)
    pygame.draw.line(out, mark, (x - 4, y - 4), (x + 4, y + 4), 2)
    pygame.draw.line(out, mark, (x + 4, y - 4), (x - 4, y + 4), 2)
    return out


def running_sprite(sprite, color, phase):
    """Return one of two vertical, grounded running poses.

    Each leg keeps the same hip position.  One is extended to the ground while
    the other is lifted; the next frame swaps them.  This matches the compact
    up/down Chrome gait and avoids side-to-side sliding.
    """
    out = sprite.copy()
    out.fill((0, 0, 0, 0), (6, 39, 25, 9))

    if phase:
        # Left leg is planted; right leg is lifted directly beneath its hip.
        pygame.draw.rect(out, color, (9, 39, 5, 9))
        pygame.draw.rect(out, color, (8, 45, 7, 3))
        pygame.draw.rect(out, color, (20, 39, 5, 5))
        pygame.draw.rect(out, color, (19, 42, 7, 3))
    else:
        # Right leg is planted; left leg is lifted directly beneath its hip.
        pygame.draw.rect(out, color, (9, 39, 5, 5))
        pygame.draw.rect(out, color, (8, 42, 7, 3))
        pygame.draw.rect(out, color, (20, 39, 5, 9))
        pygame.draw.rect(out, color, (19, 45, 7, 3))
    return out


def jumping_sprite(sprite, color):
    """Make a clean, static airborne pose with no residual run-leg pixels."""
    out = sprite.copy()
    out.fill((0, 0, 0, 0), (6, 39, 25, 9))
    pygame.draw.rect(out, color, (9, 39, 5, 9))
    pygame.draw.rect(out, color, (8, 45, 7, 3))
    pygame.draw.rect(out, color, (20, 39, 5, 9))
    pygame.draw.rect(out, color, (19, 45, 7, 3))
    return out


def make_cactus(large, count, color):
    """Draw a cactus group procedurally (small 17x35, large 25x50 like Chrome)."""
    uw, uh = (25, 50) if large else (17, 35)
    trunk = 10 if large else 7
    surf = pygame.Surface((uw * count, uh), pygame.SRCALPHA)
    for i in range(count):
        ox = i * uw
        cx = ox + uw // 2
               
        pygame.draw.rect(surf, color, (cx - trunk // 2, 1, trunk, uh - 1), border_top_left_radius=trunk // 2, border_top_right_radius=trunk // 2)
        arm_w = 4 if large else 3
                  
        ay = int(uh * 0.42)
        pygame.draw.rect(surf, color, (ox + 1, ay, cx - ox - 1, arm_w + 1), border_radius=2)
        pygame.draw.rect(surf, color, (ox + 1, ay - int(uh * 0.22), arm_w + 1, int(uh * 0.22) + arm_w), border_radius=2)
                   
        by = int(uh * 0.30)
        pygame.draw.rect(surf, color, (cx, by, ox + uw - cx - 1, arm_w + 1), border_radius=2)
        pygame.draw.rect(surf, color, (ox + uw - arm_w - 2, by - int(uh * 0.2), arm_w + 1, int(uh * 0.2) + arm_w), border_radius=2)
    return surf


def make_cloud(color):
    s = pygame.Surface((46, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, color, (0, 8, 46, 4), border_radius=2)
    pygame.draw.rect(s, color, (6, 4, 26, 6), border_radius=3)
    pygame.draw.rect(s, color, (14, 0, 12, 6), border_radius=3)
    pygame.draw.rect(s, color, (30, 5, 12, 5), border_radius=2)
    return s


class Obstacle:
    def __init__(self, kind, x, surfs, bottom):
        self.kind = kind                                     
        self.x = float(x)
        self.surfs = surfs                               
        self.w, self.h = surfs[0].get_size()
        self.bottom = bottom                                                             
        self.y = FEET_Y - bottom - self.h
        self.frame = 0
        self.timer = 0
        self.passed = False
                                                 
        if kind == "bird":
                                                                              
                                                                              
                                                                       
            self.inset = (4, 4, 4, 5)
        else:
            self.inset = (3, 3, 3, 2)

    @property
    def hitbox(self):
        l, t, r, b = self.inset
        return pygame.Rect(int(self.x) + l, self.y + t, self.w - l - r, self.h - t - b)

    def update(self, speed):
        self.x -= speed
        if self.kind == "bird":
            self.timer += 1
            if self.timer >= 10:
                self.timer = 0
                self.frame ^= 1

    def draw(self, surf):
        surf.blit(self.surfs[self.frame % len(self.surfs)], (int(self.x), self.y))


class Game:
    def __init__(self, birds=True, seed=None):
        self.rng = random.Random(seed)
        self.birds_enabled = birds
        self.hi = 0.0
        self.fonts_ready = False
        self._build_sprites(DAY)
        self.reset()

                                                                        
    def _build_sprites(self, pal):
        fg = pal["fg"]
        self.pal = pal
        self.spr_stand = reference_sprite("dino_neck_reference.png", (44, 48), fg)
        self.spr_run = [running_sprite(self.spr_stand, fg, 0), running_sprite(self.spr_stand, fg, 1)]
        self.spr_jump = jumping_sprite(self.spr_stand, fg)
                                                                           
                                            
        duck = reference_sprite("dino_duck_reference.png", (60, 26), fg)
                                                                             
                                                                       
        self.spr_duck = [duck, pygame.transform.scale(duck, (60, 25))]
        self.spr_dead = dead_sprite(self.spr_stand, fg)
        bird = reference_sprite("bird_reference.png", (52, 32), fg)
                                                                          
                                                                          
        self.spr_bird = [bird, bird]
        self.cactus = {}
        for large in (False, True):
            for n in (1, 2, 3):
                cactus = reference_sprite("cactus_reference.png", (25, 50) if large else (17, 35), fg)
                self.cactus[(large, n)] = cactus_group(cactus, n)
        self.cloud = make_cloud(pal["cloud"])

    def reset(self):
        self.speed = START_SPEED
        self.distance = 0.0
        self.score = 0.0
        self.frames = 0
        self.crashed = False
        self.crash_timer = 0
        self.dino_y = FEET_Y - 48                      
        self.vy = 0.0
        self.jumping = False
        self.ducking = False
        self.anim = 0
        self.anim_t = 0
        self.obstacles = []
        self.next_gap = 0
        self.pass_dist = None
        self.clouds = [[self.rng.randint(100, 560), self.rng.randint(15, 60)] for _ in range(3)]
        self.ground_bits = [[self.rng.randint(0, W), self.rng.randint(3, 8), self.rng.randint(0, 2)] for _ in range(26)]
        self.flash = 0
        self.last_hundred = 0
        self.night = False
        self._build_sprites(DAY)
        self.jumps_ok = 0

                                                                                
    @property
    def on_ground(self):
        return not self.jumping

    @property
    def dino_box(self):
        x = DINO_X
        if self.ducking and not self.jumping:
            return pygame.Rect(x + 3, FEET_Y - 25, 53, 24)
                                                                            
                                                                              
        return pygame.Rect(x + 4, int(self.dino_y) + 3, 39, 43)

    def _gap(self, w):
        min_gap = round(w * self.speed + 120 * 0.6)
        return self.rng.randint(min_gap, int(min_gap * 1.5))

    def _spawn(self):
                                                                           
                                                                          
                                                                              
        allow_bird = self.birds_enabled and self.score > 150
        if allow_bird and self.rng.random() < 0.35:
                                                                         
                                                                         
            bottom = self.rng.choices([35, 80], weights=[0.72, 0.28])[0]
            o = Obstacle("bird", W + 10, self.spr_bird, bottom)
        else:
            large = self.rng.random() < 0.5
            n = self.rng.randint(1, 3)
            if n > 1 and self.speed < 6.5:
                n = 1
            o = Obstacle("cactus", W + 10, [self.cactus[(large, n)]], 0)
        self.obstacles.append(o)
        self.next_gap = self._gap(o.w)

    def step(self, jump=False, duck=False):
        """advance one 60 fps tick. Returns True while alive."""
        if self.crashed:
            self.crash_timer += 1
            return False
        self.frames += 1
                  
        if jump and not self.jumping and not self.ducking:
            self.jumping = True
            self.vy = INIT_JUMP_V - self.speed / 10.0
        self.ducking = bool(duck)
        if self.jumping:
            g = GRAVITY * (DROP_COEFF if self.ducking else 1.0)
            self.vy += g
            self.dino_y += self.vy
            if self.dino_y >= FEET_Y - 48:
                self.dino_y = FEET_Y - 48
                self.jumping = False
                self.vy = 0.0
                   
        self.anim_t += 1
        if self.anim_t >= 5:
            self.anim_t = 0
            self.anim ^= 1
                   
        self.distance += self.speed
        self.score = self.distance * SCORE_COEFF
        if self.speed < MAX_SPEED:
            self.speed += ACCEL
               
        if self.frames > 120:
            last = self.obstacles[-1] if self.obstacles else None
            if last is None or (W - (last.x + last.w)) > self.next_gap:
                self._spawn()
        for o in self.obstacles:
            o.update(self.speed)
        self.obstacles = [o for o in self.obstacles if o.x + o.w > -10]
        if self.pass_dist is not None:
            self.pass_dist += self.speed
        for o in self.obstacles:
            if not o.passed and o.hitbox.right < DINO_X + 8:
                o.passed = True
                self.pass_dist = 0.0
                         
        for c in self.clouds:
            c[0] -= self.speed * 0.2
            if c[0] < -50:
                c[0] = W + self.rng.randint(0, 100)
                c[1] = self.rng.randint(15, 60)
        for b in self.ground_bits:
            b[0] -= self.speed
            if b[0] < -10:
                b[0] = W + self.rng.randint(0, 60)
                b[1] = self.rng.randint(3, 8)
                b[2] = self.rng.randint(0, 2)
                                   
        hundred = int(self.score) // 100
        if hundred > self.last_hundred:
            self.last_hundred = hundred
            self.flash = 60
        if self.flash:
            self.flash -= 1
        night = (int(self.score) // 700) % 2 == 1
        if night != self.night:
            self.night = night
            self._build_sprites(NIGHT if night else DAY)
                   
        db = self.dino_box
        for o in self.obstacles:
            if o.x < DINO_X + 60 and db.colliderect(o.hitbox):
                self.crashed = True
                self.hi = max(self.hi, self.score)
                return False
        return True

                                                                              
    def next_obstacle(self):
        """first obstacle that has not fully passed the dinosaur."""
        db_left = DINO_X + 8
        for o in self.obstacles:
            if o.hitbox.right > db_left:
                return o
        return None

    def behind_distance(self):
        """distance travelled since the last obstacle went past the dinosaur."""
        return self.pass_dist

    def gap_to(self, o):
        return o.hitbox.left - (DINO_X + 8 + 32)                              

    def features(self):
        """what the fly 'sees' - every value is scaled to 0..1 (missing = silent)."""
        o = self.next_obstacle()
        f = {
            "speed": (self.speed - START_SPEED) / (MAX_SPEED - START_SPEED),
            "dino_y": max(0.0, (FEET_Y - 48 - self.dino_y)) / 110.0,
            "dino_vy": (self.vy + 14.0) / 28.0,
            "duck": 1.0 if self.ducking else 0.0,
                                                                           
            "bird": 1.0 if o is not None and o.kind == "bird" else 0.0,
        }
        bd = self.behind_distance()
        if bd is not None and bd < 300:
            f["behind"] = bd / 300.0
        if o is not None:
            d = self.gap_to(o)
            s = self.speed
            w_sum = o.hitbox.width + 32
            tta = d / s                                                             
            ttc = (d + w_sum) / s                                               
            if tta < 45:
                f["distance"] = (tta + 6.0) / 51.0
                f["clear"] = min(1.0, max(0.0, (ttc + 6.0) / 66.0))
                f["height"] = o.bottom / 90.0
                f["width"] = min(1.0, o.w / 80.0)
        return f

    def coach(self):
        """The 'teacher' signal (like a dopamine / feedback signal): should the
        dino be jumping / ducking right now?  Returns (jump, duck) labels."""
        o = self.next_obstacle()
        if o is None:
            return 0.0, 0.0
        d = self.gap_to(o)
        s = self.speed
                                                                                   
        if self.jumping and self.vy > 0 and d > 0:
            bd = self.behind_distance()
            if bd is not None and bd < 300:
                return 0.0, 1.0
        hb = o.hitbox
        w_sum = hb.width + 32
                                                                                
                                                                                
                                     
        trigger = max(24.0 * s - w_sum, 9.0 * s)
        if o.kind == "bird" and o.bottom >= 80:
            return 0.0, 0.0                                   
        if o.kind == "bird":
                                                                           
            return (0.0, 1.0) if d <= 13 * s else (0.0, 0.0)
        return (1.0, 0.0) if d <= trigger else (0.0, 0.0)                

                                                                                
    def _font(self):
        if not self.fonts_ready:
            self.font = pygame.font.SysFont("couriernew,consolas,dejavusansmono,monospace", 13, bold=True)
            self.font_big = pygame.font.SysFont("couriernew,consolas,dejavusansmono,monospace", 15, bold=True)
            self.fonts_ready = True

    def draw(self, surf, show_score=True):
        self._font()
        pal = self.pal
        fg = pal["fg"]
        surf.fill(pal["bg"])
        for c in self.clouds:
            surf.blit(self.cloud, (int(c[0]), int(c[1])))
                 
        pygame.draw.rect(surf, fg, (0, GROUND_Y, W, 2))
        for x, w, off in self.ground_bits:
            pygame.draw.rect(surf, fg, (int(x), GROUND_Y + 4 + off * 3, w, 1))
        for o in self.obstacles:
            o.draw(surf)
              
        if self.crashed:
            spr = self.spr_dead
        elif self.jumping:
            spr = self.spr_jump
        elif self.ducking:
            spr = self.spr_duck[self.anim]
        else:
            spr = self.spr_run[self.anim]
        if self.ducking and not self.jumping and not self.crashed:
            surf.blit(spr, (DINO_X, FEET_Y - spr.get_height()))
        else:
            surf.blit(spr, (DINO_X, int(self.dino_y)))
               
        if show_score:
            show = not (self.flash and (self.flash // 6) % 2 == 0)
            txt = f"{int(self.score):05d}" if show else ""
            hi = f"HI {int(self.hi):05d}" if self.hi > 0 else ""
            col = fg
            if txt:
                t = self.font.render(txt, False, col)
                surf.blit(t, (W - 8 - t.get_width(), 8))
            if hi:
                t = self.font.render(hi, False, (fg[0] + 40 if fg[0] < 100 else fg[0] - 40,) * 3)
                surf.blit(t, (W - 8 - 70 - 12 - t.get_width(), 8))
        if self.crashed:
            t = self.font_big.render("G A M E   O V E R", False, fg)
            surf.blit(t, ((W - t.get_width()) // 2, 44))
            cx, cy = W // 2, 78
            pygame.draw.arc(surf, fg, (cx - 11, cy - 11, 22, 22), 0.6, 6.0, 3)
            pygame.draw.polygon(surf, fg, [(cx + 6, cy - 12), (cx + 14, cy - 6), (cx + 4, cy - 3)])
