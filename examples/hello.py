import pyxel

pyxel.init(160, 120)

score: int = 0
x: int = 80
y: int = 60
speed: int = 2

def update():
    global x, y, score
    if pyxel.btn(pyxel.KEY_LEFT):
        x -= speed
    if pyxel.btn(pyxel.KEY_RIGHT):
        x += speed
    if pyxel.btn(pyxel.KEY_UP):
        y -= speed
    if pyxel.btn(pyxel.KEY_DOWN):
        y += speed
    if x < 0:
        x = 0
    if x > 152:
        x = 152
    if y < 0:
        y = 0
    if y > 112:
        y = 112
    score += 1
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

def draw():
    pyxel.cls(1)
    pyxel.rect(x, y, 8, 8, 11)
    pyxel.rectb(0, 0, 160, 120, 7)
    pyxel.text(4, 4, "Hello from Native-Pyxel", 7)

pyxel.run(update, draw)
