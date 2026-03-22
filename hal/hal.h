/*
 * hal/hal.h — Umbrella header for the pyxel-retro HAL.
 *
 * Generated C files include this with:  #include "hal/hal.h"
 * The implementation is in hal/<target>/*.c
 */

#ifndef HAL_H
#define HAL_H

/* ── Sistema ─────────────────────────────────────────────────────────────── */

void         hal_init(void);
void         hal_quit(void);
void         hal_flip(void);
unsigned int hal_frame_count(void);
void         hal_wait_cycles(unsigned int cycles);
void         hal_debug_print(const char *s);
const char  *hal_istr(int n);          /* int → decimal string (static buffer) */

/* ── Gráficos: primitivas ────────────────────────────────────────────────── */

void hal_cls  (int col);
void hal_pset (int x, int y, int col);
int  hal_pget (int x, int y);
void hal_line (int x1, int y1, int x2, int y2, int col);
void hal_rect (int x, int y, int w, int h, int col);
void hal_rectb(int x, int y, int w, int h, int col);
void hal_circ (int x, int y, int r, int col);
void hal_circb(int x, int y, int r, int col);
void hal_elli (int x, int y, int a, int b, int col);
void hal_ellib(int x, int y, int a, int b, int col);
void hal_tri  (int x1, int y1, int x2, int y2, int x3, int y3, int col);
void hal_trib (int x1, int y1, int x2, int y2, int x3, int y3, int col);
void hal_fill (int x, int y, int col);

/* ── Gráficos: blitter ───────────────────────────────────────────────────── */

void hal_blt (int x, int y, int img, int u, int v, int w, int h, int colkey);
void hal_bltm(int x, int y, int tm,  int u, int v, int w, int h, int colkey);

/* ── Texto ───────────────────────────────────────────────────────────────── */

void hal_text(int x, int y, const char *s, int col);

/* ── Input ───────────────────────────────────────────────────────────────── */

int hal_btn (int key);
int hal_btnp(int key, int hold, int period);
int hal_btnr(int key);

/* ── Sonido ──────────────────────────────────────────────────────────────── */

void hal_play    (int ch, int snd, int loop);
void hal_playm   (int msc, int loop);
void hal_stop    (int ch);
int  hal_play_pos(int ch);

/* ── Aritmética auxiliar ─────────────────────────────────────────────────── */

int hal_ipow(int base, int exp);

/*
 * Constantes de teclado: definidas en hal/<target>/input_keys.h
 * e incluidas por cada .c del target que las necesite.
 * El código generado usa HAL_KEY_* directamente (el compilador las ve
 * porque los .c del target se compilan junto con el .c generado).
 */

#endif /* HAL_H */
