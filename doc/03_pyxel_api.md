# API Pyxel soportada

## Categorías

- ✅ Soporte completo — traducción directa a HAL
- ⚠️  Soporte con adaptaciones — requiere lógica especial en el transpilador o la HAL
- 🔧 Directiva de compilación — desaparece del binario final
- ❌ No soportado

---

## Sistema / ciclo de vida

| API Pyxel | Soporte | HAL / Nota |
|---|---|---|
| `pyxel.init(w, h)` | 🔧 | Configura resolución para el asset baker y el game loop |
| `pyxel.run(update, draw)` | 🔧 | Genera game loop nativo — ver docs/05_gameloop.md |
| `pyxel.run_custom(loop)` | 🔧 | Genera main() mínimo — ver docs/05_gameloop.md |
| `pyxel.quit()` | ✅ | `hal_quit()` |
| `pyxel.show()` | ✅ | Equivale a un frame único sin bucle |
| `pyxel.flip()` | ✅ | `hal_flip()` — sincronización manual de frame |

---

## Gráficos — primitivas

Todas se traducen directamente a funciones HAL implementadas en C89 (algoritmos
clásicos: Bresenham para líneas, Midpoint circle para círculos).

| API Pyxel | Soporte | HAL |
|---|---|---|
| `cls(col)` | ✅ | `hal_cls(col)` |
| `pset(x, y, col)` | ✅ | `hal_pset(x, y, col)` |
| `pget(x, y)` | ✅ | `hal_pget(x, y)` |
| `line(x1,y1,x2,y2,col)` | ✅ | `hal_line(...)` |
| `rect(x,y,w,h,col)` | ✅ | `hal_rect(...)` |
| `rectb(x,y,w,h,col)` | ✅ | `hal_rectb(...)` |
| `circ(x,y,r,col)` | ✅ | `hal_circ(...)` |
| `circb(x,y,r,col)` | ✅ | `hal_circb(...)` |
| `elli(x,y,a,b,col)` | ✅ | `hal_elli(...)` |
| `ellib(x,y,a,b,col)` | ✅ | `hal_ellib(...)` |
| `tri(x1,y1,x2,y2,x3,y3,col)` | ✅ | `hal_tri(...)` |
| `trib(...)` | ✅ | `hal_trib(...)` |
| `fill(x,y,col)` | ✅ | `hal_fill(...)` — flood fill en RAM de vídeo |

---

## Gráficos — sprites y tilemap

| API Pyxel | Soporte | Nota |
|---|---|---|
| `blt(x,y,img,u,v,w,h,[colkey])` | ⚠️ | Copia desde `IMG_BANK_N` (array estático en ROM generado por baker) |
| `bltm(x,y,tm,u,v,w,h,[colkey])` | ⚠️ | Copia desde `TILEMAP_N` (array estático en ROM) |
| `text(x,y,s,col)` | ⚠️ | Solo strings literales estáticos. Font embebida en HAL |

El parámetro `colkey` (color transparente) se soporta: el blitter comprueba el
índice de color y salta el pixel si coincide con `colkey`.

---

## Input

| API Pyxel | Soporte | HAL / Nota |
|---|---|---|
| `btn(key)` | ✅ | `hal_btn(key)` |
| `btnp(key,[hold],[period])` | ✅ | `hal_btnp(key, hold, period)` — edge detection con auto-repeat |
| `btnr(key)` | ✅ | `hal_btnr(key)` — released |
| `mouse_x` | ❌ | Sin ratón estándar en targets de 8 bits |
| `mouse_y` | ❌ | Idem |
| `mouse_wheel` | ❌ | Idem |

### Constantes de teclas / botones

Se define un mapeo de las constantes `pyxel.KEY_*` y `pyxel.GAMEPAD*` a los
códigos nativos de cada target en `hal/*/input.h`. El transpilador sustituye
`pyxel.KEY_Q` por la constante HAL correspondiente.

---

## Sonido

| API Pyxel | Soporte | Nota |
|---|---|---|
| `play(ch, snd, [tick], [loop])` | ✅ | `hal_play(ch, snd, loop)` |
| `playm(msc, [tick], [loop])` | ⚠️ | Soportado si la música está definida en el .pyxres |
| `stop([ch])` | ✅ | `hal_stop(ch)` |
| `play_pos(ch)` | ✅ | `hal_play_pos(ch)` |

Los datos de sonido provienen exclusivamente del asset baker (definidos en
`.pyxres`). No se soporta generación procedural de sonido en runtime desde Python
(sería necesario manipular directamente los registros del SID/beeper desde HAL).

---

## Assets

| API Pyxel | Soporte | Nota |
|---|---|---|
| `pyxel.load(filename)` | 🔧 | Directiva de compilación — ver docs/06_assets.md |
| `pyxel.save(filename)` | ❌ | Sin sistema de archivos en ROM/cinta |
| `images[n]` | ⚠️ | Acceso de solo lectura al banco de imagen N (array ROM) |
| `tilemaps[n]` | ⚠️ | Acceso de solo lectura al tilemap N (array ROM) |
| `sounds[n]` | ⚠️ | Acceso de solo lectura a la definición de sonido N |
| `musics[n]` | ⚠️ | Acceso de solo lectura |

---

## Variables de sistema (solo lectura)

| Variable Pyxel | Soporte | Nota |
|---|---|---|
| `pyxel.width` | ✅ | Constante en compilación (del `pyxel.init`) |
| `pyxel.height` | ✅ | Constante en compilación |
| `pyxel.frame_count` | ✅ | `hal_frame_count()` — contador de frames |
| `pyxel.fps` | ✅ | Constante en compilación |

---

## No soportado

| API Pyxel | Razón |
|---|---|
| `screen` (objeto Image) | Sin framebuffer accesible como objeto en 8 bits |
| `mouse_*` | Sin ratón estándar |
| `pyxel.save()` | Sin filesystem en runtime |
| `run_with_profiler()` | Sin utilidad en el target |
| `capture_*` | Sin sentido en hardware retro |
| Clases `Image`, `Tilemap`, `Sound`, `Music` como objetos Python | Se accede a sus datos como arrays ROM, no como objetos |
