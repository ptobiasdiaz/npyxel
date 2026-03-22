import pyxel

# Screen: 160×120 px
pyxel.init(160, 120)

# ── Constants ────────────────────────────────────────────────────────────────
PAD_H:   int = 20    # paddle height
PAD_W:   int = 4     # paddle width
BALL_SZ: int = 4     # ball side
PAD_SPD: int = 2     # paddle speed (px/frame)
MARGIN:  int = 4     # paddle distance from edge

# ── State ────────────────────────────────────────────────────────────────────
# Ball
bx: int = 78         # ball x
by: int = 58         # ball y
bdx: int = 2         # ball velocity x
bdy: int = 1         # ball velocity y

# Paddles (y = top edge)
ly: int = 50         # left paddle y
ry: int = 50         # right paddle y

# Score
ls: int = 0          # left score
rs: int = 0          # right score

# Flash counter for goal event
flash: int = 0

def _clamp(v: int, lo: int, hi: int) -> int:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v

def update():
    global bx, by, bdx, bdy, ly, ry, ls, rs, flash

    # ── Paddles ──────────────────────────────────────────────────────────────
    if pyxel.btn(pyxel.KEY_W):
        ly -= PAD_SPD
    if pyxel.btn(pyxel.KEY_S):
        ly += PAD_SPD
    ly = _clamp(ly, 0, 120 - PAD_H)

    if pyxel.btn(pyxel.KEY_UP):
        ry -= PAD_SPD
    if pyxel.btn(pyxel.KEY_DOWN):
        ry += PAD_SPD
    ry = _clamp(ry, 0, 120 - PAD_H)

    # ── Ball ─────────────────────────────────────────────────────────────────
    if flash > 0:
        flash -= 1
    else:
        bx += bdx
        by += bdy

        # Top / bottom wall bounce
        if by <= 0:
            by = 0
            bdy = -bdy
        if by >= 120 - BALL_SZ:
            by = 120 - BALL_SZ
            bdy = -bdy

        # Left paddle collision
        if (bx <= MARGIN + PAD_W and
                bx >= MARGIN and
                by + BALL_SZ >= ly and
                by <= ly + PAD_H):
            bx = MARGIN + PAD_W
            bdx = -bdx
            # Nudge bdy based on contact point
            if by + BALL_SZ // 2 < ly + PAD_H // 2:
                bdy = -1
            else:
                bdy = 1

        # Right paddle collision
        if (bx + BALL_SZ >= 160 - MARGIN - PAD_W and
                bx + BALL_SZ <= 160 - MARGIN and
                by + BALL_SZ >= ry and
                by <= ry + PAD_H):
            bx = 160 - MARGIN - PAD_W - BALL_SZ
            bdx = -bdx
            if by + BALL_SZ // 2 < ry + PAD_H // 2:
                bdy = -1
            else:
                bdy = 1

        # Goal: ball exits left
        if bx < 0:
            rs += 1
            bx = 78
            by = 58
            bdx = 2
            bdy = 1
            flash = 20

        # Goal: ball exits right
        if bx > 160:
            ls += 1
            bx = 78
            by = 58
            bdx = -2
            bdy = -1
            flash = 20

    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

def draw():
    pyxel.cls(0)

    # Centre dashed line
    i: int = 0
    for i in range(15):
        pyxel.rect(79, i * 8 + 1, 2, 5, 5)

    # Paddles
    pyxel.rect(MARGIN, ly, PAD_W, PAD_H, 7)
    pyxel.rect(160 - MARGIN - PAD_W, ry, PAD_W, PAD_H, 7)

    # Ball (hidden during flash)
    if flash == 0 or flash % 4 < 2:
        pyxel.rect(bx, by, BALL_SZ, BALL_SZ, 11)

    # Score
    pyxel.text(55, 4, str(ls), 7)
    pyxel.text(98, 4, str(rs), 7)

    # Border
    pyxel.rectb(0, 0, 160, 120, 5)

pyxel.run(update, draw)
