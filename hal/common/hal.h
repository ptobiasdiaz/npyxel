/*
 * hal/common/hal.h — Hardware Abstraction Layer contract
 *
 * Contrato C89 uniforme que implementa cada target.
 * El código generado por el transpilador NUNCA accede a hardware directamente:
 * todo pasa por funciones hal_*.
 *
 * Generado por pyxel-retro. No editar manualmente.
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

int hal_ipow(int base, int exp);    /* base^exp entero */

/* ── Constantes de teclado (definidas en hal/<target>/input_keys.h) ──────── */
/*
 * Cada target define HAL_KEY_A … HAL_KEY_Z, HAL_KEY_0 … HAL_KEY_9,
 * HAL_KEY_UP, HAL_KEY_DOWN, HAL_KEY_LEFT, HAL_KEY_RIGHT,
 * HAL_KEY_SPACE, HAL_KEY_RETURN, HAL_KEY_ESCAPE, HAL_KEY_BACKSPACE,
 * HAL_KEY_TAB,
 * HAL_GP1_A, HAL_GP1_B, HAL_GP1_UP, HAL_GP1_DOWN,
 * HAL_GP1_LEFT, HAL_GP1_RIGHT
 */

#endif /* HAL_H */
