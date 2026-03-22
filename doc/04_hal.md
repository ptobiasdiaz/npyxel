# Hardware Abstraction Layer (HAL)

## Principio

La HAL define un contrato C89 uniforme que el código generado por el transpilador
llama independientemente del target. Cada target implementa ese contrato de la
forma más eficiente posible para su hardware.

**El código generado por el transpilador nunca accede a hardware directamente.**
Todo pasa por funciones `hal_*`.

---

## Niveles de implementación

Cada función HAL puede implementarse en tres niveles según su criticidad:

| Nivel | Cuándo usarlo | Ejemplo |
|---|---|---|
| C89 puro | I/O no crítico en tiempo | `hal_rectb`, `hal_text` |
| C89 + inline ASM | Timing semi-crítico, registros de hardware | `hal_cls`, `hal_pset` |
| ASM puro | Timing ciclo-exacto, IRQ handlers | `hal_play` en C64 (SID) |

---

## Estructura de directorios

```
hal/
├── common/
│   ├── hal.h              # contrato completo — todas las firmas hal_*
│   ├── bresenham.c        # algoritmos de dibujo portables (C89 puro)
│   └── font_5x3.h         # font embebida para hal_text
├── c64/
│   ├── graphics.c         # VIC-II: pset, cls, rect, blt, ...
│   ├── sound.c            # SID: play, stop, ...
│   ├── input.c            # CIA: btn, btnp
│   ├── gameloop.c         # raster IRQ, VBL sync
│   └── input_keys.h       # mapeo pyxel.KEY_* → scancodes C64
├── cpm/
│   ├── graphics.c         # salida por consola ANSI o terminal CP/M
│   ├── sound.c            # beeper básico via puerto de salida
│   ├── input.c            # BDOS call para input de teclado
│   ├── gameloop.c         # timing por ciclos de CPU
│   └── input_keys.h
└── zx/
    ├── graphics.c         # ULA: atributos 8x8, pixel directo
    ├── sound.c            # beeper 1 bit via puerto 0xFE
    ├── input.c            # lectura de matriz de teclado
    ├── gameloop.c         # HALT para sincronización a 50Hz
    └── input_keys.h
```

---

## Contrato: `hal/common/hal.h`

```c
#ifndef HAL_H
#define HAL_H

/* ── Sistema ─────────────────────────────────────────── */
void hal_init(void);
void hal_quit(void);
void hal_flip(void);
unsigned int hal_frame_count(void);

/* ── Gráficos: primitivas ────────────────────────────── */
void hal_cls(int col);
void hal_pset(int x, int y, int col);
int  hal_pget(int x, int y);
void hal_line(int x1, int y1, int x2, int y2, int col);
void hal_rect(int x, int y, int w, int h, int col);
void hal_rectb(int x, int y, int w, int h, int col);
void hal_circ(int x, int y, int r, int col);
void hal_circb(int x, int y, int r, int col);
void hal_elli(int x, int y, int a, int b, int col);
void hal_ellib(int x, int y, int a, int b, int col);
void hal_tri(int x1, int y1, int x2, int y2, int x3, int y3, int col);
void hal_trib(int x1, int y1, int x2, int y2, int x3, int y3, int col);
void hal_fill(int x, int y, int col);

/* ── Gráficos: blitter ───────────────────────────────── */
void hal_blt(int x, int y, int img, int u, int v, int w, int h, int colkey);
void hal_bltm(int x, int y, int tm, int u, int v, int w, int h, int colkey);

/* ── Texto ───────────────────────────────────────────── */
void hal_text(int x, int y, const char *s, int col);

/* ── Input ───────────────────────────────────────────── */
int hal_btn(int key);
int hal_btnp(int key, int hold, int period);
int hal_btnr(int key);

/* ── Sonido ──────────────────────────────────────────── */
void hal_play(int ch, int snd, int loop);
void hal_playm(int msc, int loop);
void hal_stop(int ch);
int  hal_play_pos(int ch);

#endif /* HAL_H */
```

---

## Notas de implementación por target

### C64

**Gráficos (VIC-II)**
- Modo bitmap multicolor (160×200, 4 colores por celda 4×8) o hires (320×200, 2 colores por celda 8×8)
- `hal_pset` escribe directamente en el bitmap en $A000 y actualiza el color RAM en $D800
- `hal_cls` limpia ambas áreas con memset — candidato a inline ASM para velocidad
- El blitter (`hal_blt`) copia desde arrays ROM con comprobación de `colkey`

**Sonido (SID $D400)**
- `hal_play` programa las 3 voces del SID según los datos de `SOUND_N_*` del asset baker
- Implementación en ASM puro recomendada para timing correcto del envelope ADSR
- Canal 3 de Pyxel → voz de ruido del SID (registro de control 0x80)

**Input (CIA1 $DC00/$DC01)**
- Joystick en puerto 2 (más común): lectura directa del registro $DC00
- Teclado: matriz de 8×8 vía $DC00/$DC01

**Game loop**
- Raster IRQ en línea 251 (debajo del área visible)
- Ver docs/05_gameloop.md

### ZX Spectrum

**Gráficos (ULA)**
- Pixel buffer en $4000–$57FF (6144 bytes, organización no lineal por tercios)
- Atributos de color en $5800–$5AFF (768 bytes, celdas de 8×8)
- `hal_pset` debe calcular la dirección no lineal: requiere inline ASM o lógica de bits cuidadosa
- Solo 2 colores por celda de 8×8 → limitación inherente del hardware

**Sonido (beeper)**
- 1 bit via bit 4 del puerto $FE
- Generación de tonos por software (bit-banging) — timing ciclo-exacto necesario
- Implementar en ASM puro

**Game loop**
- Instrucción `HALT` espera la siguiente interrupción del modo-I (50Hz en PAL)

### CP/M

**Gráficos**
- Sin hardware gráfico estándar — emulación via escape codes ANSI si el terminal lo soporta
- Alternativa: asumir hardware gráfico específico (RC2014 con VDP TMS9918, etc.)
- Configurable en `targets/cpm.py` con un parámetro `--display`

**Sonido**
- Beeper básico via puerto de salida (dependiente del hardware específico)

**Game loop**
- Sin VBL — timing por conteo de ciclos o polling de timer del sistema

---

## Algoritmos portables (hal/common/bresenham.c)

Las siguientes funciones se implementan una sola vez en C89 puro y llaman a
`hal_pset` internamente. Todos los targets las heredan:

- `hal_line` — algoritmo de Bresenham
- `hal_circ` / `hal_circb` — algoritmo de Midpoint circle
- `hal_elli` / `hal_ellib` — elipse por ecuación paramétrica entera
- `hal_tri` / `hal_trib` — triángulo relleno por scanline
- `hal_rectb` — cuatro llamadas a `hal_line`
- `hal_fill` — flood fill iterativo (sin recursión — stack limitado en 8 bits)
- `hal_text` — renderizado de la font 5×3 embebida pixel a pixel via `hal_pset`

Cada target puede sobreescribir cualquiera de estas con una implementación
optimizada si lo necesita (por ejemplo, `hal_rect` en C64 puede usar operaciones
de bloque del VIC-II en lugar de pixel a pixel).
