"""Generates the Japanese haunted-house (obake yashiki) 32x32 tileset.

Output: assets/tileset/Tiles.png  (8 x 8 tiles, 256 x 256 px)

Everything is drawn procedurally from a fixed palette and fixed seeds, so the
output is deterministic. Tweak a tile function and re-run:

    python tools/gen_haunted_tileset.py

Tile index = row * 8 + col.

 row 0  wood TL | wood T  | wood TR | stone TL | stone T | stone TR | plat L   | plat M
 row 1  wood L  | wood C  | wood R  | stone L  | stone C | stone R  | plat R   | wood T (broken)
 row 2  wood BL | wood B  | wood BR | stone BL | stone B | stone BR | wood C 2 | stone C 2 (mossy)
 row 3  plaster | beam    | pillar  | shoji    | shoji torn | shoji hand | fusuma | baseboard
 row 4  roof L  | roof M  | roof R  | roof fill| roof eave | round window | barred window | wall hole
 row 5  chochin | chochin-obake | kasa-obake | stone lantern | candle | ofuda | scroll | cobweb L
 row 6  shimenawa | grave | sotoba | bamboo spikes | hitodama 1 | hitodama 2 | hitodama 3 | hitodama 4
 row 7  jizo | well | susuki grass | mokumokuren shoji | cobweb R | broken plates | hanging roots | debris

Rows 0-2 are solid terrain (two 9-slice sets plus a one-way platform).
Rows 3-4 are opaque background tiles. Rows 5-7 are transparent props that
are meant to be drawn over the background (hitodama is a 4 frame loop).
"""

import math
import os
import random

from PIL import Image

T = 32
COLS, ROWS = 8, 8

# ---------------------------------------------------------------- palette
# Pulled from / matched to the character sprites: deep purple-navy darks,
# reddish woods, cool slate stone, muted teal moss and warm lantern light.
CLEAR = (0, 0, 0, 0)
OUT = (20, 16, 19)          # outline, same as the sprites
VOID = (12, 10, 16)         # holes / darkness

W0 = (32, 21, 28)           # wood ramp, dark -> light
W1 = (54, 33, 42)
W2 = (80, 48, 52)
W3 = (110, 68, 62)
W4 = (146, 98, 78)
W5 = (186, 140, 104)

S0 = (20, 18, 29)           # stone ramp
S1 = (38, 38, 54)
S2 = (58, 60, 82)
S3 = (82, 86, 110)
S4 = (112, 118, 146)
S5 = (163, 167, 194)

M0 = (28, 40, 44)           # moss
M1 = (40, 64, 62)
M2 = (56, 90, 80)
M3 = (92, 124, 96)

P0 = (22, 19, 30)           # plaster wall (background, kept dark)
P1 = (32, 28, 42)
P2 = (42, 37, 54)
P3 = (54, 48, 68)

PA0 = (62, 62, 86)          # shoji paper (moonlit, dim)
PA1 = (82, 84, 110)
PA2 = (100, 102, 130)

BONE = (223, 224, 232)
CREAM = (228, 210, 170)
TAN = (160, 134, 98)
RED = (173, 47, 69)
RED_D = (120, 29, 79)
PINK = (189, 106, 98)
ORANGE = (255, 174, 112)
GOLD = (240, 181, 65)
EMBER = (171, 81, 48)
FLAME = (255, 236, 170)
SKY = (18, 20, 40)
SKY2 = (27, 36, 71)
MOON = (245, 255, 232)
MOON2 = (200, 210, 214)

SP0 = (60, 100, 170)        # spirit fire
SP1 = (100, 170, 220)
SP2 = (180, 230, 245)
SP3 = (245, 255, 250)

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def dither(x, y, t):
    """True when an ordered-dither pattern at (x, y) should be 'on' for level t in [0,1]."""
    return (BAYER[y % 4][x % 4] + 0.5) / 16.0 < t


def periodic_noise(seed, cells=4, size=T):
    """Smooth value noise that wraps every `size` pixels in x and y."""
    r = random.Random(seed)
    g = [[r.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            fx, fy = x * cells / size, y * cells / size
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
            a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
            b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


class Tile:
    def __init__(self, w=T, h=T):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), CLEAR)
        self.px = self.im.load()

    # -- primitives
    def set(self, x, y, c, a=255):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if len(c) == 4:
            c, a = c[:3], c[3]
        if a >= 255:
            self.px[x, y] = tuple(c) + (255,)
            return
        r, g, b, da = self.px[x, y]
        t = a / 255
        if da == 0:
            self.px[x, y] = tuple(c) + (a,)
        else:
            self.px[x, y] = mix((r, g, b), c, t) + (max(da, a),)

    def get(self, x, y):
        return self.px[x % self.w, y % self.h]

    def opaque(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.px[x, y][3] > 0

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = CLEAR

    def rect(self, x0, y0, x1, y1, c, a=255):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c, a)

    def line(self, x0, y0, x1, y1, c, a=255):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, c, a)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c, a=255):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, c, a)

    def outline(self, c=OUT, diagonal=False):
        """Adds a 1px outline outside every opaque pixel."""
        pts = []
        nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonal:
            nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for y in range(self.h):
            for x in range(self.w):
                if self.px[x, y][3] == 0 and any(self.opaque(x + dx, y + dy) for dx, dy in nb):
                    pts.append((x, y))
        for x, y in pts:
            self.set(x, y, c)
        return self

    def paste(self, other, x=0, y=0):
        self.im.alpha_composite(other.im, (x, y))
        self.px = self.im.load()
        return self

    def copy(self):
        t = Tile(self.w, self.h)
        t.im = self.im.copy()
        t.px = t.im.load()
        return t

    def flipped(self):
        t = Tile(self.w, self.h)
        t.im = self.im.transpose(Image.FLIP_LEFT_RIGHT)
        t.px = t.im.load()
        return t

    def darken_rows(self, y0, y1, amount):
        """Blend rows [y0, y1] toward OUT, strongest at y0 (cast shadow)."""
        n = max(1, y1 - y0 + 1)
        for i, y in enumerate(range(y0, y1 + 1)):
            t = amount * (1 - i / n)
            for x in range(self.w):
                r, g, b, a = self.px[x, y]
                if a:
                    self.px[x, y] = mix((r, g, b), OUT, t) + (a,)


# ================================================================ terrain

def wood_base(seed=1, knot=False, crack=False):
    """Vertical skirt boards, 8px wide, seamless in both directions."""
    r = random.Random(seed)
    t = Tile()
    for bx in range(0, T, 8):
        tone = r.choice([W2, W2, mix(W2, W1, 0.35), mix(W2, W3, 0.2)])
        t.rect(bx, 0, bx + 7, T - 1, tone)
        t.rect(bx, 0, bx, T - 1, W0)                      # seam
        t.rect(bx + 1, 0, bx + 1, T - 1, mix(tone, W3, 0.6))
        t.rect(bx + 7, 0, bx + 7, T - 1, mix(tone, W1, 0.5))
        # grain: wavy vertical lines that wrap vertically
        for _ in range(2):
            gx = bx + r.randint(2, 6)
            ph = r.random() * math.tau
            for y in range(T):
                x = gx + round(math.sin(ph + y * math.tau / T * 2) * 0.8)
                if r.random() < 0.8 and bx + 2 <= x <= bx + 6:
                    t.set(x, y, mix(tone, W1, 0.7))
    if knot:
        kx, ky = 19, 12
        t.ellipse(kx + 0.5, ky + 0.5, 2.2, 3.2, W1)
        t.ellipse(kx + 0.5, ky + 0.5, 1.0, 1.6, W0)
        t.set(kx - 1, ky - 2, W3)
    if crack:
        pts = [(4, 18), (5, 20), (5, 22), (6, 24), (6, 27)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t.line(x0, y0, x1, y1, W0)
        t.set(13, 7, S4)   # nail heads
        t.set(13, 25, S4)
    return t


def wood_top(t, broken=False):
    """Polished floor beam across the top; the surface catches the moonlight."""
    rows = [OUT, W5, W4, W3, W3, W3, W3, W3, W2, W1, OUT]
    for y, c in enumerate(rows):
        t.rect(0, y, T - 1, y, c)
    # horizontal grain
    r = random.Random(7)
    for _ in range(9):
        x, y, n = r.randrange(T), r.randint(3, 7), r.randint(3, 8)
        for i in range(n):
            t.set((x + i) % T, y, mix(W3, W2, 0.7))
    # plank joint + nails
    t.rect(24, 1, 24, 9, W1)
    t.rect(25, 2, 25, 9, W4)
    t.set(22, 5, S4)
    t.set(27, 5, S4)
    t.darken_rows(11, 13, 0.55)
    if broken:
        # a splintered missing chunk of the beam
        hole = {12: 3, 13: 5, 14: 6, 15: 6, 16: 7, 17: 7, 18: 6, 19: 4, 20: 2}
        for x, d in hole.items():
            for y in range(0, d + 2):
                t.set(x, y, VOID if y > 0 else CLEAR)
            t.clear(x, 0)
            t.set(x, d + 2, OUT)
        for x in (11, 21):
            t.set(x, 1, W4)
            t.set(x, 0, OUT)
        t.set(12, 1, W4)
        t.set(20, 1, W4)
        for x in range(12, 21):  # re-outline the new top edge of the hole
            if not t.opaque(x, 0) and t.opaque(x, 1):
                t.set(x, 1, OUT)
        t.line(13, 9, 16, 9, W3)
        t.set(17, 9, W4)
    return t


def wood_side(t, right):
    x0 = 26 if right else 0
    cols = [OUT, W4, W3, W3, W2, OUT] if not right else [OUT, W4, W3, W3, W2, OUT]
    for i, c in enumerate(cols):
        t.rect(x0 + i, 0, x0 + i, T - 1, c)
    return t


def wood_bottom(t):
    t.rect(0, 25, T - 1, 25, OUT)
    t.rect(0, 26, T - 1, 26, W3)
    t.rect(0, 27, T - 1, 29, W1)
    t.rect(0, 30, T - 1, 30, W0)
    t.rect(0, 31, T - 1, 31, OUT)
    t.darken_rows(22, 24, 0.0)
    return t


def round_corner(t, corner, top):
    """Clip a 2px rounded corner; `top` is the first solid row for top corners."""
    if corner == "tl":
        t.clear(0, top); t.clear(1, top); t.clear(0, top + 1)
        t.set(1, top + 1, OUT); t.set(2, top, OUT)
    elif corner == "tr":
        t.clear(31, top); t.clear(30, top); t.clear(31, top + 1)
        t.set(30, top + 1, OUT); t.set(29, top, OUT)
    elif corner == "bl":
        t.clear(0, 31); t.clear(1, 31); t.clear(0, 30)
        t.set(1, 30, OUT)
    elif corner == "br":
        t.clear(31, 31); t.clear(30, 31); t.clear(31, 30)
        t.set(30, 30, OUT)


def wood_tile(top=False, bottom=False, left=False, right=False, base=None):
    t = (base or wood_base()).copy()
    if bottom:
        wood_bottom(t)
    if left:
        wood_side(t, False)
    if right:
        wood_side(t, True)
    if top:
        wood_top(t)
        # beam end grain where it overhangs a pillar
        if left:
            t.rect(0, 1, 0, 9, OUT); t.rect(1, 2, 1, 8, W4); t.set(2, 5, W3)
        if right:
            t.rect(31, 1, 31, 9, OUT); t.rect(30, 2, 30, 8, W2)
    if top and left:
        round_corner(t, "tl", 0)
    if top and right:
        round_corner(t, "tr", 0)
    if bottom and left:
        round_corner(t, "bl", 0)
    if bottom and right:
        round_corner(t, "br", 0)
    return t


def stone_base(seed=3, moss=0.0):
    """Irregular ishigaki stones via toroidal Voronoi, seamless both ways."""
    r = random.Random(seed)
    seeds = []
    for gy in range(3):
        for gx in range(3):
            seeds.append((gx * 32 / 3 + r.uniform(1, 9), gy * 32 / 3 + r.uniform(1, 9)))
    ids = [[0] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            best, bi = 1e9, 0
            for i, (sx, sy) in enumerate(seeds):
                dx = min(abs(x - sx), T - abs(x - sx))
                dy = min(abs(y - sy), T - abs(y - sy)) * 1.35
                d = dx * dx + dy * dy
                if d < best:
                    best, bi = d, i
            ids[y][x] = bi
    tones = [r.choice([S2, S3, mix(S2, S3, 0.5), mix(S3, S4, 0.25)]) for _ in seeds]
    speck = periodic_noise(seed + 11, 8)
    mnoise = periodic_noise(seed + 23, 8)
    t = Tile()

    def mortar(x, y):
        i = ids[y % T][x % T]
        return ids[y % T][(x + 1) % T] != i or ids[(y + 1) % T][x % T] != i

    for y in range(T):
        for x in range(T):
            if mortar(x, y):
                t.set(x, y, S0)
                continue
            c = tones[ids[y][x]]
            if mortar(x, y - 1) or mortar(x - 1, y):
                c = mix(c, S5, 0.35)
            elif mortar(x, y + 1) or mortar(x + 1, y):
                c = mix(c, S1, 0.6)
            elif speck[y][x] > 0.72 and dither(x, y, 0.4):
                c = mix(c, S1, 0.45)
            if moss and mnoise[y][x] > 1 - moss and dither(x, y, (mnoise[y][x] - (1 - moss)) * 4):
                c = M1 if mnoise[y][x] < 1 - moss / 2 else M2
            t.set(x, y, c)
    return t


def stone_top(t, left=False, right=False):
    r = random.Random(5)
    thick = periodic_noise(9, 4)
    drips = {3: 4, 11: 2, 17: 5, 26: 3}
    t.rect(0, 0, T - 1, 1, CLEAR)
    for x in range(T):
        m = 5 + int(thick[0][x] * 3) + drips.get(x, 0)
        t.set(x, 2, OUT)
        t.set(x, 3, M3 if dither(x, 3, 0.75) else M2)
        for y in range(4, m + 1):
            t.set(x, y, M2 if dither(x, y, 0.55 - (y - 4) * 0.1) else M1)
        t.set(x, m + 1, M0)
    # grass blades poking up
    for x in (1, 5, 6, 13, 20, 21, 28):
        h = r.randint(1, 2)
        for y in range(2 - h, 2):
            t.set(x, y, M2)
        t.set(x, 2, M1)
    if left:
        for y in range(3, 12):
            t.set(1, y, M2 if y < 8 else M1)
    if right:
        for y in range(3, 10):
            t.set(30, y, M1)
    return t


def stone_tile(top=False, bottom=False, left=False, right=False, base=None):
    t = (base or stone_base()).copy()
    top_row = 2 if top else 0
    if left:
        t.rect(0, top_row, 0, T - 1, OUT)
        for y in range(top_row, T):
            r, g, b, a = t.px[1, y]
            t.px[1, y] = mix((r, g, b), S5, 0.25) + (255,)
    if right:
        t.rect(31, top_row, 31, T - 1, OUT)
        for y in range(top_row, T):
            r, g, b, a = t.px[30, y]
            t.px[30, y] = mix((r, g, b), OUT, 0.35) + (255,)
    if bottom:
        t.rect(0, 31, T - 1, 31, OUT)
        for x in range(T):
            r, g, b, a = t.px[x, 30]
            t.px[x, 30] = mix((r, g, b), OUT, 0.4) + (255,)
    if top:
        stone_top(t, left, right)
        if left:
            t.rect(0, 2, 0, T - 1, OUT)
        if right:
            t.rect(31, 2, 31, T - 1, OUT)
    if top and left:
        round_corner(t, "tl", 2)
    if top and right:
        round_corner(t, "tr", 2)
    if bottom and left:
        round_corner(t, "bl", 0)
    if bottom and right:
        round_corner(t, "br", 0)
    return t


def platform(part):
    """One-way wooden beam; rope lashings at the ends."""
    t = Tile()
    rows = [OUT, W5, W4, W3, W3, W3, W2, W1, OUT]
    for y, c in enumerate(rows):
        t.rect(0, y, T - 1, y, c)
    for x in range(0, T, 5):
        t.set(x + 2, 4, mix(W3, W2, 0.6))
        t.set(x + 3, 4, mix(W3, W2, 0.6))
    if part in ("l", "r"):
        # beam end + rope lashing + hanging support rope
        end = 0 if part == "l" else 31
        inner = 1 if part == "l" else -1
        t.rect(end, 1, end, 7, OUT)
        t.rect(end + inner, 1, end + inner, 7, W4 if part == "l" else W2)
        t.clear(end, 0); t.clear(end, 8)
        lx = 5 if part == "l" else 23
        for x in range(lx, lx + 4):
            for y in range(0, 9):
                t.set(x, y, TAN if (x + y) % 3 else CREAM)
            t.set(x, -1 + 0, OUT)
        t.rect(lx - 1, 0, lx - 1, 8, OUT)
        t.rect(lx + 4, 0, lx + 4, 8, OUT)
        # little iron bracket peg under the beam
        bx = 3 if part == "l" else 26
        t.rect(bx, 9, bx + 2, 11, S2)
        t.set(bx, 9, S4)
        t.rect(bx - 1, 9, bx - 1, 11, OUT); t.rect(bx + 3, 9, bx + 3, 11, OUT)
        t.rect(bx - 1, 12, bx + 3, 12, OUT)
    else:
        # a wisp of cobweb under the middle
        for i, (x, y) in enumerate([(12, 9), (13, 10), (14, 10), (15, 11), (16, 11), (17, 10), (18, 10), (19, 9)]):
            t.set(x, y, S5, 110)
        t.set(15, 12, S5, 70)
        t.set(16, 13, S5, 60)
    return t


# ================================================================ background

def plaster(seed=21, stains=False):
    t = Tile()
    n = periodic_noise(seed, 4)
    n2 = periodic_noise(seed + 1, 8)
    for y in range(T):
        for x in range(T):
            v = n[y][x] * 0.7 + n2[y][x] * 0.3
            c = P1
            if dither(x, y, (v - 0.45) * 2.5):
                c = P2
            if dither(x, y, (0.4 - v) * 2.5):
                c = P0
            t.set(x, y, c)
    if stains:
        r = random.Random(seed)
        # a hairline crack
        x, y = 7, 3
        for _ in range(9):
            nx, ny = x + r.choice([-1, 0, 1]), y + 2
            t.line(x, y, nx, ny, P0)
            x, y = nx, ny
        t.set(x + 1, y - 1, P3)
        # water streak
        for y in range(0, 20):
            if dither(23, y, 1 - y / 20):
                t.set(23, y, P0)
            if dither(24, y, 0.6 - y / 25):
                t.set(24, y, P0)
    return t


def beam_wall():
    t = plaster(22)
    rows = [W0, W2, W3, W2, W2, W1, W1, OUT]
    for y, c in enumerate(rows):
        t.rect(0, y + 1, T - 1, y + 1, c)
    t.rect(0, 0, T - 1, 0, OUT)
    t.darken_rows(9, 11, 0.5)
    # a hanging ofuda tag nailed to the beam
    return t


def baseboard():
    t = plaster(24)
    t.darken_rows(20, 23, 0.0)
    t.rect(0, 23, T - 1, 23, OUT)
    t.rect(0, 24, T - 1, 24, W3)
    t.rect(0, 25, T - 1, 29, W1)
    t.rect(0, 30, T - 1, 31, W0)
    for x in range(0, T, 16):
        t.rect(x, 25, x, 31, W0)
    for x in range(T):
        if dither(x, 22, 0.35):
            t.set(x, 22, P0)
    return t


def pillar():
    t = plaster(25, stains=False)
    cols = [OUT, W4, W3, W3, W3, W2, W2, W2, W2, W1, W1, OUT]
    for i, c in enumerate(cols):
        t.rect(10 + i, 0, 10 + i, T - 1, c)
    # cast shadow on the wall to the right
    for y in range(T):
        for x in (22, 23):
            if x == 22 or dither(x, y, 0.5):
                t.set(x, y, P0)
    # grain + an old nail
    for y in range(0, T, 5):
        t.set(13 + (y // 5) % 3, y, W2)
    t.set(15, 14, S4); t.set(15, 15, S2)
    return t


def shoji(variant=None):
    t = Tile()
    n = periodic_noise(31, 4)
    for y in range(T):
        for x in range(T):
            v = n[y][x]
            c = PA1
            if dither(x, y, (v - 0.5) * 2):
                c = PA2
            if dither(x, y, (0.35 - v) * 2):
                c = PA0
            t.set(x, y, c)

    if variant == "hand":
        # shadow of a long-fingered hand pressed against the paper from behind
        sh = mix(PA0, P0, 0.55)
        t.ellipse(15.5, 22.5, 6.5, 7, sh)
        fingers = [(9, 17, 7, 5), (12, 15, 11, 2), (16, 15, 16, 1), (19, 16, 21, 3), (21, 20, 26, 16)]
        for fx0, fy0, fx1, fy1 in fingers:
            t.line(fx0, fy0, fx1, fy1, sh)
            t.line(fx0 + 1, fy0, fx1 + 1, fy1, sh)
        t.rect(12, 28, 19, 31, sh)
        # fainter second hand behind
        for fx0, fy0, fx1, fy1 in [(3, 12, 2, 6), (5, 11, 5, 5)]:
            t.line(fx0, fy0, fx1, fy1, mix(PA0, P0, 0.3))

    # kumiko lattice: bars on x=0,15 and y=0,10,21 (period 32 -> seamless)
    lat = W1
    for x in (0, 15, 16):
        t.rect(x, 0, x, T - 1, lat)
    for y in (0, 10, 21):
        t.rect(0, y, T - 1, y, lat)
    for x in (1, 17):
        t.rect(x, 0, x, T - 1, mix(PA0, lat, 0.4))  # soft lattice shadow

    if variant == "torn":
        holes = [(3, 12, 9, 17), (19, 23, 26, 29), (22, 2, 25, 5)]
        r = random.Random(4)
        for x0, y0, x1, y1 in holes:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = (x1 - x0) / 2 + 0.5, (y1 - y0) / 2 + 0.5
            for y in range(y0 - 1, y1 + 2):
                for x in range(x0 - 1, x1 + 2):
                    d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                    if d < 1 - r.random() * 0.35 and t.get(x, y)[:3] != lat:
                        t.set(x, y, VOID)
        # paper flaps curling out of the holes
        t.line(9, 17, 11, 19, PA2); t.set(12, 20, BONE)
        t.line(19, 29, 18, 31, PA2)
        t.set(4, 17, PA2); t.set(5, 18, PA2)
    return t


def mokumokuren():
    """Shoji whose torn cells are full of staring eyes."""
    t = shoji("torn")
    for ex, ey in [(6, 14), (22, 26), (23, 3), (8, 4), (26, 14)]:
        # eye socket in the dark
        t.ellipse(ex + 0.5, ey + 0.5, 3.6, 2.1, VOID)
        t.ellipse(ex + 0.5, ey + 0.5, 2.8, 1.3, BONE)
        t.set(ex - 2, ey, mix(BONE, PINK, 0.5))
        t.set(ex + 3, ey, mix(BONE, PINK, 0.5))
        t.set(ex, ey, RED)
        t.set(ex + 1, ey, OUT)
        t.set(ex, ey + 1, RED_D)
        t.set(ex + 1, ey + 1, OUT)
    return t


def fusuma():
    t = Tile()
    base = (66, 58, 74)
    for y in range(T):
        for x in range(T):
            t.set(x, y, base)
    # faded seigaiha (wave) pattern, period 16
    for cy in range(0, T + 8, 8):
        off = 8 if (cy // 8) % 2 else 0
        for cx in range(-16 + off, T + 16, 16):
            for rr, col in ((7.5, (84, 74, 92)), (5.5, base), (4.5, (80, 70, 88)), (2.5, base)):
                for y in range(cy - 8, cy + 1):
                    for x in range(cx - 8, cx + 9):
                        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                        if rr - 1 < d <= rr:
                            t.set(x % T, y % T, col)
    # lacquered frame on the sides
    for x, c in ((0, OUT), (1, W1), (30, W1), (31, OUT)):
        t.rect(x, 0, x, T - 1, c)
    # round hikite pull
    t.ellipse(26, 16, 2.6, 2.6, OUT)
    t.ellipse(26, 16, 1.8, 1.8, GOLD)
    t.ellipse(26, 16, 1.0, 1.0, EMBER)
    return t


def kawara_pattern(t, y_from=0):
    """Hongawara roof: rounded cover tiles (lx 1-4) over flat pan tiles
    (lx 6-7), laid in courses 8px tall. Seamless every 8px."""
    cover = {0: S0, 1: S4, 2: S3, 3: S3, 4: S2, 5: S0, 6: mix(S1, S0, 0.4), 7: S1}
    for y in range(y_from, T):
        for x in range(T):
            lx, ly = x % 8, y % 8
            c = cover[lx]
            is_cover = 1 <= lx <= 4
            if ly == 0 and is_cover:
                c = mix(c, S1, 0.45)          # emerging from under the course above
            if ly == 6 and lx in (1, 4):
                c = S0                        # rounded end of the cover tile
            if ly == 7:
                c = S0 if is_cover or lx in (0, 5) else mix(S1, S0, 0.6)
            if ly == 6 and lx in (6, 7):
                c = mix(S1, S0, 0.3)
            t.set(x, y, c)


def roof(part):
    t = Tile()
    kawara_pattern(t, 0)
    if part in ("l", "m", "r"):
        # ridge cap (walkable)
        rows = [OUT, S4, S3, S3, S2, S1, OUT]
        for y, c in enumerate(rows):
            t.rect(0, y, T - 1, y, c)
        for x in range(4, T, 8):
            t.set(x, 2, S5)
        t.darken_rows(7, 9, 0.5)
        if part in ("l", "r"):
            # onigawara end block with a tomoe disc; drawn for the left end, mirrored for the right
            end = Tile()
            end.rect(0, 1, 9, 14, S2)
            end.rect(1, 1, 8, 1, S4)
            end.rect(0, 1, 0, 14, S3)
            end.rect(9, 1, 9, 14, S1)
            end.rect(0, 14, 9, 14, S1)
            end.ellipse(5, 8, 3.4, 3.4, S0)
            end.ellipse(5, 8, 2.6, 2.6, S3)
            end.ellipse(4.5, 7.5, 1.2, 1.2, S4)
            end.set(5, 9, S1); end.set(6, 8, S1)
            end.clear(0, 1); end.clear(9, 1)
            end.outline()
            if part == "r":
                end = end.flipped()
            t.clear(0 if part == "l" else 31, 0)
            t.paste(end)
    if part == "eave":
        # tile ends: round caps along the bottom edge
        t.rect(0, 22, T - 1, T - 1, CLEAR)
        for cx in range(0, T, 8):
            t.ellipse(cx + 3.5, 23.5, 3.6, 3.6, OUT)
            t.ellipse(cx + 3.5, 23.5, 2.7, 2.7, S3)
            t.ellipse(cx + 3.5, 23.5, 1.2, 1.2, S1)
            t.set(cx + 2, 22, S4)
        for x in range(T):
            if t.opaque(x, 27) is False and t.opaque(x, 26):
                pass
    return t


def window(kind):
    t = plaster(27, stains=False)
    if kind == "round":
        cx, cy = 16, 16
        t.ellipse(cx, cy, 14, 14, OUT)
        t.ellipse(cx, cy, 13, 13, W3)
        t.ellipse(cx, cy, 11, 11, OUT)
        t.ellipse(cx, cy, 10, 10, SKY)
        for y in range(6, 27):
            for x in range(6, 27):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) < 10 and dither(x, y, (26 - y) / 40):
                    t.set(x, y, SKY2)
        t.ellipse(16, 13, 5.5, 5.5, MOON2)
        t.ellipse(16.5, 12.5, 4.8, 4.8, MOON)
        t.set(15, 11, MOON2); t.set(18, 14, MOON2); t.set(17, 10, MOON2)
        # thin cloud across the moon
        t.rect(9, 16, 22, 16, SKY2)
        t.rect(12, 17, 19, 17, SKY2)
        # bamboo bars
        for x in (10, 23):
            for y in range(6, 27):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) < 10.5:
                    t.set(x, y, W1)
                    t.set(x - 1, y, W2 if y % 6 else W0)
        # top-left rim highlight
        for a in range(200, 290, 6):
            x = cx + 13.5 * math.cos(math.radians(a))
            y = cy + 13.5 * math.sin(math.radians(a))
            t.set(int(x), int(y), W4)
    else:
        t.rect(4, 3, 27, 28, OUT)
        t.rect(5, 4, 26, 27, W3)
        t.rect(6, 5, 25, 26, W1)
        t.rect(7, 6, 24, 25, SKY)
        for y in range(6, 26):
            for x in range(7, 25):
                if dither(x, y, (25 - y) / 30):
                    t.set(x, y, SKY2)
        for y in range(6, 26):  # moon glow
            for x in range(7, 25):
                d = math.hypot(x - 14.5, y - 11.5)
                if d < 9 and dither(x, y, (9 - d) / 14):
                    t.set(x, y, (54, 62, 100))
        t.ellipse(14.5, 11.5, 4.4, 4.4, MOON2)
        t.ellipse(14.5, 11.5, 3.6, 3.6, MOON)
        # bare branch silhouetted across the moon
        t.line(24, 8, 17, 13, OUT); t.line(17, 13, 8, 16, OUT)
        t.line(19, 12, 20, 17, OUT); t.line(13, 14, 11, 19, OUT)
        t.line(21, 10, 23, 13, OUT)
        # bars
        for x in (11, 18):
            t.rect(x, 6, x + 1, 25, W1)
            t.rect(x, 6, x, 25, W3)
        t.rect(5, 4, 26, 4, W4)
        t.rect(3, 29, 28, 29, OUT)
        t.rect(4, 28, 27, 28, W4)
    return t


def wall_hole():
    t = plaster(28, stains=True)
    r = random.Random(12)
    cx, cy = 15, 17
    for y in range(T):
        for x in range(T):
            a = math.atan2(y - cy, x - cx)
            rad = 9 + math.sin(a * 5) * 1.6 + math.sin(a * 3 + 1) * 1.2
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.1)
            if d < rad:
                t.set(x, y, VOID)
            elif d < rad + 1.2:
                t.set(x, y, P3 if y < cy else P0)
    # exposed bamboo lath (komai): a sparse woven diagonal lattice
    for y in range(T):
        for x in range(T):
            if t.get(x, y)[:3] != VOID:
                continue
            if (x + y) % 6 == 0:
                t.set(x, y, (74, 64, 46))
            elif (x - y) % 6 == 0:
                t.set(x, y, (54, 46, 36))
    # crumbs at the bottom of the hole
    for _ in range(6):
        x, y = r.randint(8, 22), r.randint(25, 29)
        if t.get(x, y)[:3] in (P0, P1, P2):
            t.set(x, y, P3)
    return t


# ================================================================ props

def chochin():
    t = Tile()
    t.rect(15, 0, 16, 3, OUT)
    t.rect(10, 4, 21, 6, W0)
    t.rect(11, 4, 20, 4, W2)
    for y in range(7, 26):
        dy = (y - 16) / 9.5
        hw = int(round(9.2 * math.sqrt(max(0, 1 - dy * dy * 0.8))))
        for x in range(16 - hw, 16 + hw):
            u = abs(x + 0.5 - 16) / max(hw, 1)
            v = abs(y - 15.5) / 10
            glow = 1 - (u * u + v * v)
            c = RED
            if glow > 0.25:
                c = PINK
            if glow > 0.55:
                c = ORANGE
            if glow > 0.8:
                c = FLAME
            if u > 0.8:
                c = RED_D
            if y % 3 == 0:
                c = mix(c, RED_D, 0.45)
            t.set(x, y, c)
    # a painted character: stylised "spirit" mark
    for x, y in [(15, 11), (16, 11), (14, 13), (17, 13), (15, 14), (16, 14), (15, 16), (16, 16), (15, 17), (13, 19), (18, 19), (14, 20), (17, 20), (15, 20), (16, 20)]:
        t.set(x, y, OUT)
    t.rect(10, 26, 21, 28, W0)
    t.rect(11, 28, 20, 28, W2)
    t.set(16, 29, GOLD)
    t.set(16, 30, EMBER)
    t.outline()
    return t


def chochin_obake():
    t = Tile()
    t.rect(15, 0, 16, 2, OUT)
    t.rect(10, 3, 21, 5, W0)
    for y in range(6, 27):
        dy = (y - 16) / 10.5
        hw = int(round(9.5 * math.sqrt(max(0, 1 - dy * dy * 0.75))))
        for x in range(16 - hw, 16 + hw):
            u = abs(x + 0.5 - 16) / max(hw, 1)
            c = CREAM if u < 0.55 else TAN
            if y % 3 == 0:
                c = mix(c, (120, 96, 72), 0.5)
            t.set(x, y, c)
    # one huge eye
    t.ellipse(14, 12, 4.2, 3.4, OUT)
    t.ellipse(14, 12, 3.3, 2.5, BONE)
    t.rect(14, 11, 15, 13, OUT)
    t.set(14, 11, RED)
    # small squinting second eye
    t.line(20, 11, 22, 12, OUT)
    # torn mouth + lolling tongue
    for x in range(9, 24):
        yy = 19 + round(math.sin((x - 9) / 14 * math.pi) * 2)
        for y in range(yy - 1, yy + 2):
            t.set(x, y, OUT if y != yy else RED_D)
    for y in range(20, 30):
        w = 2 if y < 27 else 1
        for x in range(16 - w + (y > 26), 16 + w):
            t.set(x + (y - 20) // 4, y, RED if x > 15 - w else PINK)
    t.set(17, 24, PINK); t.set(18, 27, PINK)
    # rip in the paper
    t.line(22, 7, 24, 11, OUT)
    t.rect(10, 27, 21, 28, W0)
    t.outline()
    return t


def kasa_obake():
    t = Tile()
    # closed paper umbrella canopy
    for y in range(2, 21):
        hw = int((y - 1) * 0.62)
        for x in range(16 - hw, 17 + hw):
            rib = (x - 16) % 4 == 0
            c = RED if x < 16 else RED_D
            if rib:
                c = mix(c, OUT, 0.35)
            if x == 16 - hw:
                c = PINK
            t.set(x, y, c)
    t.rect(15, 0, 17, 1, W1)
    t.set(16, 0, W3)
    # scalloped hem
    for x in range(5, 28):
        if x % 3 == 0:
            t.set(x, 21, RED_D)
    # the eye
    t.ellipse(16.5, 10.5, 3.6, 3.0, OUT)
    t.ellipse(16.5, 10.5, 2.6, 2.0, BONE)
    t.rect(16, 10, 17, 11, OUT)
    t.set(16, 10, GOLD)
    # mouth + tongue flapping out sideways
    t.rect(13, 15, 20, 15, OUT)
    t.rect(14, 16, 19, 16, OUT)
    for i, (x, y) in enumerate([(19, 16), (20, 17), (21, 17), (22, 18), (23, 18), (24, 19), (24, 20)]):
        t.set(x, y, RED if i % 2 else PINK)
        t.set(x, y + 1, RED_D)
    # single leg on a geta
    t.rect(15, 22, 17, 27, CREAM)
    t.rect(15, 22, 15, 27, TAN)
    t.rect(14, 26, 18, 27, CREAM)
    t.rect(11, 28, 21, 29, W3)
    t.rect(11, 28, 21, 28, W4)
    t.rect(12, 30, 13, 30, W1)
    t.rect(19, 30, 20, 30, W1)
    t.outline()
    return t


def toro():
    t = Tile()
    t.rect(16, 1, 17, 2, S3)             # hoju
    t.rect(15, 3, 18, 4, S3)
    for y in range(5, 11):              # roof
        hw = 3 + (y - 5) * 2
        t.rect(16 - hw, y, 17 + hw, y, S3 if y < 9 else S2)
        t.set(16 - hw, y, S4)
    t.rect(4, 10, 29, 10, S1)
    t.rect(9, 11, 24, 18, S2)           # firebox
    t.rect(12, 12, 21, 17, OUT)
    t.rect(13, 13, 20, 17, EMBER)
    t.rect(14, 13, 19, 16, ORANGE)
    t.rect(15, 14, 18, 15, FLAME)
    t.rect(16, 12, 17, 17, S2)          # window bar
    t.rect(8, 19, 25, 20, S3)
    t.rect(13, 21, 20, 26, S2)          # post
    t.rect(13, 21, 13, 26, S3)
    t.rect(20, 21, 20, 26, S1)
    t.rect(9, 27, 24, 29, S2)           # base
    t.rect(9, 27, 24, 27, S3)
    t.rect(7, 30, 26, 30, S1)
    # moss
    for x, y in [(10, 27), (11, 27), (22, 28), (14, 21), (6, 9), (7, 9), (8, 9), (25, 20)]:
        t.set(x, y, M2)
    t.outline()
    # warm light spilling out
    for (x, y) in [(11, 13), (11, 15), (22, 13), (22, 15)]:
        t.set(x, y, ORANGE, 90)
    return t


def candle():
    t = Tile()
    # glow
    for y in range(0, 14):
        for x in range(8, 24):
            d = math.hypot(x - 15.5, (y - 5) * 1.2)
            if d < 7.5 and dither(x, y, (7.5 - d) / 12):
                t.set(x, y, ORANGE, 70)
    t.ellipse(15.5, 5.5, 1.8, 3.4, EMBER)
    t.ellipse(15.5, 6, 1.3, 2.5, ORANGE)
    t.rect(15, 5, 16, 7, FLAME)
    t.set(15, 2, ORANGE)
    t.set(15, 9, OUT)
    t.rect(14, 10, 17, 17, BONE)         # candle
    t.rect(17, 10, 17, 17, S5)
    t.set(14, 11, CREAM); t.set(14, 12, CREAM)  # wax drip
    t.rect(11, 18, 20, 18, W1)           # dish
    t.rect(12, 19, 19, 19, W0)
    t.rect(15, 20, 16, 28, W1)           # stand
    t.rect(15, 20, 15, 28, W3)
    t.rect(12, 29, 19, 30, W1)
    t.rect(11, 31, 20, 31, W0)
    t.rect(12, 29, 19, 29, W3)
    t.outline()
    return t


def ofuda():
    t = Tile()
    strips = [(7, 3, 0), (15, 1, 1), (22, 5, -1)]
    for sx, sy, lean in strips:
        for y in range(sy, sy + 22):
            off = (y - sy) * lean // 10
            for x in range(sx, sx + 5):
                c = CREAM if x < sx + 4 else TAN
                t.set(x + off, y, c)
            if (y - sy) in (3, 6, 7, 10, 11, 12, 15, 18):
                t.set(sx + 1 + off + (y % 2), y, OUT)
                t.set(sx + 2 + off, y, OUT)
            if (y - sy) in (4, 14):
                t.set(sx + 2 + off, y, RED)
                t.set(sx + 1 + off, y, RED)
        t.set(sx + 2, sy, S3)  # pin
    # torn bottom corner of the middle one
    t.clear(18, 22); t.clear(19, 22); t.clear(19, 21)
    t.outline()
    return t


def kakejiku():
    t = Tile()
    t.line(16, 0, 11, 3, OUT)
    t.line(16, 0, 21, 3, OUT)
    t.rect(8, 3, 23, 4, W1)
    t.set(7, 3, GOLD); t.set(24, 3, GOLD)
    t.rect(9, 5, 22, 27, (78, 60, 52))       # mounting silk
    t.rect(11, 7, 20, 25, (150, 136, 112))   # aged paper
    for y in range(7, 26):
        for x in range(11, 21):
            if dither(x, y, 0.2 + (y - 7) / 60):
                t.set(x, y, (132, 118, 96))
    # painted yurei: black hair, white robe, fading to nothing at the feet
    t.rect(14, 9, 17, 11, OUT)
    t.rect(13, 11, 13, 16, OUT)
    t.rect(18, 11, 18, 17, OUT)
    t.rect(15, 11, 16, 12, BONE)
    t.set(15, 12, OUT)
    for y in range(13, 25):
        for x in range(14, 18 + (y > 16)):
            if dither(x, y, 1 - (y - 13) / 13):
                t.set(x, y, BONE)
    t.rect(12, 16, 13, 17, BONE)          # dangling hands
    t.set(12, 18, BONE)
    t.rect(9, 27, 22, 28, W0)
    t.set(8, 28, GOLD); t.set(23, 28, GOLD)
    t.outline()
    return t


def cobweb():
    t = Tile()
    col = S5
    rays = [0, 18, 38, 58, 78, 90]
    for a in rays:
        for d in range(0, 30):
            x = d * math.cos(math.radians(a))
            y = d * math.sin(math.radians(a))
            if x < T and y < T:
                t.set(int(x), int(y), col, 150 - d * 3)
    for rr in (6, 12, 18, 24):
        pts = []
        for a in rays:
            pts.append((rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            # sagging thread between rays
            for i in range(0, 9):
                u = i / 8
                sag = math.sin(u * math.pi) * rr * 0.12
                x = x0 + (x1 - x0) * u - sag * 0.7
                y = y0 + (y1 - y0) * u - sag * 0.7
                t.set(int(x), int(y), col, 150 - rr * 3)
    # a small spider
    t.set(13, 13, OUT); t.set(14, 14, OUT); t.set(13, 14, EMBER)
    for dx, dy in [(-1, 0), (2, 0), (-1, 2), (2, 2)]:
        t.set(13 + dx, 13 + dy, OUT)
    return t


def shimenawa():
    t = Tile()
    # twisted straw rope, period 8 -> seamless
    for y in range(2, 11):
        for x in range(T):
            ph = (x + y) % 8
            c = CREAM if ph < 3 else (TAN if ph < 6 else (120, 96, 72))
            if y in (2, 10):
                c = mix(c, (100, 80, 60), 0.5)
            t.set(x, y, c)
    t.rect(0, 1, T - 1, 1, OUT)
    t.rect(0, 11, T - 1, 11, OUT)
    # zig-zag shide paper streamer
    t.rect(15, 12, 16, 12, BONE)
    for i in range(4):
        x0, y0 = (14 if i % 2 == 0 else 16), 13 + i * 3
        t.rect(x0, y0, x0 + 3, y0 + 2, BONE)
        t.rect(x0, y0 + 2, x0 + 3, y0 + 2, S5)          # fold shadow
    # straw tassels
    for x in (4, 5, 6, 26, 27, 28):
        t.rect(x, 12, x, 16 + (x % 3), TAN)
    t.outline()
    t.clear(0, 12); t.clear(31, 12)
    for x in range(T):  # rope is seamless: no outline on the tile edges
        for y in range(2, 11):
            pass
    return t


def grave():
    t = Tile()
    t.rect(10, 5, 21, 25, S2)
    t.rect(11, 4, 20, 4, S2)
    t.rect(10, 5, 11, 25, S3)
    t.rect(20, 5, 21, 25, S1)
    t.rect(11, 4, 18, 4, S4)
    # engraved characters
    for y in (8, 9, 12, 13, 14, 17, 18, 21):
        t.set(15, y, S0)
        if y in (9, 13, 18):
            t.set(14, y, S0); t.set(16, y, S0)
    # crack + moss
    t.line(19, 6, 17, 11, S0)
    for x, y in [(10, 22), (10, 23), (11, 24), (12, 25), (20, 24), (21, 23)]:
        t.set(x, y, M2)
    t.rect(6, 26, 25, 28, S2)
    t.rect(6, 26, 25, 26, S3)
    t.rect(5, 29, 26, 30, S1)
    # offering cup and incense stick
    t.rect(7, 23, 8, 25, S4)
    t.set(8, 21, EMBER)
    t.line(8, 22, 8, 25, TAN)
    t.outline()
    t.set(8, 19, S5, 90); t.set(9, 17, S5, 60)
    return t


def sotoba():
    t = Tile()
    boards = [(8, 4, 0), (14, 1, 1), (20, 5, 0)]
    for bx, top, lean in boards:
        for y in range(top, 31):
            off = (31 - y) // 12 * lean
            t.rect(bx + off, y, bx + 3 + off, y, TAN if y > top + 1 else CREAM)
            t.set(bx + 3 + off, y, (120, 96, 72))
        # gorinto notches near the top
        for ny in (top + 3, top + 6):
            t.clear(bx, ny)
            t.clear(bx + 3, ny)
        for y in range(top + 9, 28, 3):
            t.set(bx + 1 + (31 - y) // 12 * lean, y, OUT)
            t.set(bx + 2 + (31 - y) // 12 * lean, y + 1, OUT)
    t.outline()
    return t


def bamboo_spikes():
    t = Tile()
    stakes = [(2, 14), (8, 10), (14, 16), (19, 9), (25, 13)]
    for sx, top in stakes:
        for y in range(top, 32):
            for x in range(sx, sx + 5):
                c = M2 if x == sx + 1 else (M1 if x < sx + 4 else M0)
                t.set(x, y, c)
            if (y - top) % 7 == 6:
                t.rect(sx, y, sx + 4, y, M0)
                t.set(sx + 1, y - 1, M3)
        # diagonal cut: sharp tip on the left side
        for i in range(0, 5):
            for y in range(top, top + 5 - i):
                t.clear(sx + 4 - i + 0, y) if i else None
        for i in range(5):
            y = top + 4 - i
            for x in range(sx + i + 1, sx + 5):
                t.clear(x, y - 1)
            t.set(sx + i, y, CREAM if i < 4 else TAN)
    t.outline()
    return t


def hitodama(frame):
    t = Tile()
    ph = frame * math.tau / 4
    cx, cy = 16, 21
    # flickering tail rising upward
    for y in range(1, cy + 1):
        u = (cy - y) / (cy - 1)
        w = 5.4 * (1 - u) ** 0.9
        sway = math.sin(ph + u * 4.0) * 3.2 * u
        for x in range(T):
            d = abs(x + 0.5 - (cx + sway))
            if d < w:
                k = 1 - d / max(w, 0.01)
                c = SP0
                if k > 0.35:
                    c = SP1
                if k > 0.7 and u < 0.55:
                    c = SP2
                a = 255 if u < 0.7 else int(255 * (1 - u) / 0.3)
                t.set(x, y, c, a)
    # head
    pulse = [0, 0.4, 0.2, 0.6][frame]
    t.ellipse(cx, cy, 6 + pulse, 6 + pulse, SP0)
    t.ellipse(cx, cy, 5 + pulse, 5, SP1)
    t.ellipse(cx - 0.5, cy - 0.5, 3.5, 3.3, SP2)
    t.ellipse(cx - 1, cy - 1, 1.8, 1.8, SP3)
    # soft outer halo
    for y in range(T):
        for x in range(T):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 6.5 + pulse < d < 9 and dither(x + frame, y, 0.35) and not t.opaque(x, y):
                t.set(x, y, SP1, 90)
    # detached sparks
    for i in range(3):
        a = ph * 1.3 + i * 2.1
        sx = cx + math.sin(a) * 7
        sy = 12 - ((frame * 3 + i * 5) % 11)
        t.set(int(sx), int(sy), SP2, 200)
    return t


def jizo():
    t = Tile()
    t.ellipse(16, 10, 5, 5.2, S3)          # head
    t.ellipse(15, 9, 3.5, 3.5, S4)
    t.line(13, 10, 14, 10, S1)            # closed eyes
    t.line(17, 10, 18, 10, S1)
    t.set(15, 12, S2); t.set(16, 12, S2)
    t.ellipse(16, 22, 7.5, 8, S2)          # body
    t.ellipse(14.5, 21, 5, 6, S3)
    t.rect(9, 27, 23, 30, S1)
    # red bib (yodarekake)
    for y in range(15, 22):
        hw = 6 - abs(y - 15) // 2 if y > 17 else 6
        t.rect(16 - hw, y, 15 + hw, y, RED if y < 20 else RED_D)
    t.rect(10, 15, 21, 15, PINK)
    # red knit cap
    t.ellipse(16, 6.5, 5.2, 3, RED)
    t.rect(11, 7, 21, 7, RED_D)
    t.set(16, 3, PINK)
    # hands in prayer
    t.rect(15, 22, 16, 25, S4)
    t.outline()
    for x, y in [(9, 26), (22, 27), (10, 29)]:
        t.set(x, y, M2)
    return t


def well():
    t = Tile()
    # posts + roof beam + pulley
    t.rect(4, 3, 6, 20, W2); t.rect(4, 3, 4, 20, W3)
    t.rect(25, 3, 27, 20, W2); t.rect(25, 3, 25, 20, W3)
    t.rect(2, 2, 29, 4, W1); t.rect(2, 2, 29, 2, W4)
    t.ellipse(16, 7, 2.6, 2.6, W0)
    t.set(16, 7, S4)
    t.line(16, 9, 16, 13, TAN)
    t.rect(13, 13, 18, 16, W3)             # bucket
    t.rect(13, 14, 18, 14, S3)
    t.rect(13, 13, 13, 16, W4)
    # stone ring (front view of a cylinder)
    for y in range(17, 31):
        for x in range(3, 29):
            u = (x - 3) / 25
            c = mix(S3, S1, abs(u - 0.35) * 1.3)
            if (y - 17) % 5 == 4 or (x + ((y - 17) // 5) * 4) % 8 == 0:
                c = S0
            t.set(x, y, c)
    t.ellipse(16, 17.5, 13, 2.5, S4)
    t.ellipse(16, 17.5, 11, 1.6, VOID)
    # something pale reaching over the rim...
    t.rect(20, 15, 22, 17, BONE)
    t.set(20, 14, BONE); t.set(22, 14, BONE)
    t.set(21, 18, BONE)
    t.outline()
    # a cracked plate at the foot of the well
    return t


def susuki():
    t = Tile()
    blades = [(6, 31, 2, 10, -1), (10, 31, 9, 5, 1), (14, 31, 17, 3, 1), (18, 31, 24, 7, 1), (22, 31, 28, 12, 1), (12, 31, 6, 14, -1)]
    for x0, y0, x1, y1, _ in blades:
        steps = y0 - y1
        for i in range(steps + 1):
            u = i / steps
            x = x0 + (x1 - x0) * (u ** 2)
            y = y0 - i
            t.set(int(round(x)), y, M1 if i < steps * 0.6 else M2)
    plumes = [(9, 5), (17, 3), (24, 7), (2, 10)]
    for px, py in plumes:
        for i in range(7):
            x = px + (1 if i > 3 else 0) - (1 if i < 2 else 0)
            y = py + i
            t.set(x, y, CREAM)
            if i % 2:
                t.set(x + 1, y, BONE)
                t.set(x - 1, y + 1, TAN)
    t.outline(M0)
    return t


def plates():
    t = Tile()
    plate = (200, 206, 224)
    blue = (70, 90, 150)
    for i, y in enumerate((27, 25, 23, 21)):
        t.ellipse(12, y, 8, 2, plate)
        t.rect(5, y, 19, y, blue if i % 2 == 0 else mix(plate, blue, 0.4))
    t.ellipse(12, 20.5, 6, 1.4, BONE)
    t.set(10, 20, blue); t.set(14, 21, blue)
    # broken shards scattered to the right
    for sx, sy in [(22, 28), (26, 29), (24, 25)]:
        t.rect(sx, sy, sx + 2, sy, plate)
        t.set(sx + 1, sy - 1, plate)
        t.set(sx + 2, sy, blue)
    t.outline()
    return t


def roots():
    t = Tile()
    r = random.Random(3)
    for x0 in (4, 11, 19, 26):
        x = x0
        length = r.randint(14, 28)
        for y in range(0, length):
            if r.random() < 0.25:
                x += r.choice([-1, 1])
            t.set(x, y, W1 if y < length - 4 else W2)
            if y < 6:
                t.set(x + 1, y, W0)
            if r.random() < 0.08:
                t.set(x + 1, y + 1, W2)
                t.set(x + 2, y + 2, W2)
    t.outline()
    return t


def debris():
    t = Tile()
    t.line(2, 29, 14, 25, W3)              # broken board
    t.line(2, 30, 14, 26, W2)
    t.line(3, 31, 14, 27, W1)
    t.set(15, 25, W4); t.set(16, 24, W4)   # splinters
    t.set(15, 27, W4)
    t.rect(19, 27, 27, 30, S2)             # fallen roof tile
    t.rect(19, 27, 27, 27, S3)
    t.rect(21, 28, 25, 28, S1)
    for x, y in [(8, 31), (17, 31), (29, 31), (12, 30), (18, 30)]:
        t.set(x, y, P3)
    t.outline()
    return t


# ================================================================ sheet

def build():
    wb = wood_base()
    sb = stone_base()
    L, R, U, D = "left", "right", "top", "bottom"

    def w(*sides):
        return wood_tile(**{s: True for s in sides}, base=wb)

    def s(*sides):
        return stone_tile(**{s: True for s in sides}, base=sb)

    sheet = [
        [w(U, L), w(U), w(U, R), s(U, L), s(U), s(U, R), platform("l"), platform("m")],
        [w(L), w(), w(R), s(L), s(), s(R), platform("r"), wood_top(wb.copy(), broken=True)],
        [w(D, L), w(D), w(D, R), s(D, L), s(D), s(D, R), wood_base(1, knot=True, crack=True), stone_base(3, moss=0.3)],
        [plaster(), beam_wall(), pillar(), shoji(), shoji("torn"), shoji("hand"), fusuma(), baseboard()],
        [roof("l"), roof("m"), roof("r"), roof("fill"), roof("eave"), window("round"), window("barred"), wall_hole()],
        [chochin(), chochin_obake(), kasa_obake(), toro(), candle(), ofuda(), kakejiku(), cobweb()],
        [shimenawa(), grave(), sotoba(), bamboo_spikes(), hitodama(0), hitodama(1), hitodama(2), hitodama(3)],
        [jizo(), well(), susuki(), mokumokuren(), cobweb().flipped(), plates(), roots(), debris()],
    ]
    img = Image.new("RGBA", (COLS * T, ROWS * T), CLEAR)
    for ry, row in enumerate(sheet):
        for cx, tile in enumerate(row):
            img.alpha_composite(tile.im, (cx * T, ry * T))
    return img


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "tileset", "Tiles.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build().save(out)
    print("wrote", out)
