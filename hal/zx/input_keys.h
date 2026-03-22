/*
 * hal/zx/input_keys.h — ZX Spectrum 48K keyboard matrix constants.
 *
 * Key encoding: (row_index << 3) | bit_in_row
 *   row_index 0-7 maps to ZX half-row ports (bit 0 = key closest to center)
 *   bit = 0 means PRESSED (active low), 0-4 valid
 *
 * Half-row port map (high byte → low byte always 0xFE):
 *   Row 0  port 0xFEFE: CAPS SHIFT, Z, X, C, V
 *   Row 1  port 0xFDFE: A, S, D, F, G
 *   Row 2  port 0xFBFE: Q, W, E, R, T
 *   Row 3  port 0xF7FE: 1, 2, 3, 4, 5
 *   Row 4  port 0xEFFE: 0, 9, 8, 7, 6
 *   Row 5  port 0xDFFE: P, O, I, U, Y
 *   Row 6  port 0xBFFE: ENTER, L, K, J, H
 *   Row 7  port 0x7FFE: SPACE, SYM SHIFT, M, N, B
 */

#ifndef ZX_INPUT_KEYS_H
#define ZX_INPUT_KEYS_H

/* ── Row 0: CAPS SHIFT, Z, X, C, V ──────────────────────────────────────── */
#define HAL_KEY_SHIFT   ( 0*8 | 0 )
#define HAL_KEY_Z       ( 0*8 | 1 )
#define HAL_KEY_X       ( 0*8 | 2 )
#define HAL_KEY_C       ( 0*8 | 3 )
#define HAL_KEY_V       ( 0*8 | 4 )

/* ── Row 1: A, S, D, F, G ────────────────────────────────────────────────── */
#define HAL_KEY_A       ( 1*8 | 0 )
#define HAL_KEY_S       ( 1*8 | 1 )
#define HAL_KEY_D       ( 1*8 | 2 )
#define HAL_KEY_F       ( 1*8 | 3 )
#define HAL_KEY_G       ( 1*8 | 4 )

/* ── Row 2: Q, W, E, R, T ────────────────────────────────────────────────── */
#define HAL_KEY_Q       ( 2*8 | 0 )
#define HAL_KEY_W       ( 2*8 | 1 )
#define HAL_KEY_E       ( 2*8 | 2 )
#define HAL_KEY_R       ( 2*8 | 3 )
#define HAL_KEY_T       ( 2*8 | 4 )

/* ── Row 3: 1, 2, 3, 4, 5 ────────────────────────────────────────────────── */
#define HAL_KEY_1       ( 3*8 | 0 )
#define HAL_KEY_2       ( 3*8 | 1 )
#define HAL_KEY_3       ( 3*8 | 2 )
#define HAL_KEY_4       ( 3*8 | 3 )
#define HAL_KEY_5       ( 3*8 | 4 )

/* ── Row 4: 0, 9, 8, 7, 6 ────────────────────────────────────────────────── */
#define HAL_KEY_0       ( 4*8 | 0 )
#define HAL_KEY_9       ( 4*8 | 1 )
#define HAL_KEY_8       ( 4*8 | 2 )
#define HAL_KEY_7       ( 4*8 | 3 )
#define HAL_KEY_6       ( 4*8 | 4 )

/* ── Row 5: P, O, I, U, Y ────────────────────────────────────────────────── */
#define HAL_KEY_P       ( 5*8 | 0 )
#define HAL_KEY_O       ( 5*8 | 1 )
#define HAL_KEY_I       ( 5*8 | 2 )
#define HAL_KEY_U       ( 5*8 | 3 )
#define HAL_KEY_Y       ( 5*8 | 4 )

/* ── Row 6: ENTER, L, K, J, H ────────────────────────────────────────────── */
#define HAL_KEY_RETURN  ( 6*8 | 0 )
#define HAL_KEY_L       ( 6*8 | 1 )
#define HAL_KEY_K       ( 6*8 | 2 )
#define HAL_KEY_J       ( 6*8 | 3 )
#define HAL_KEY_H       ( 6*8 | 4 )

/* ── Row 7: SPACE, SYM SHIFT, M, N, B ───────────────────────────────────── */
#define HAL_KEY_SPACE   ( 7*8 | 0 )
#define HAL_KEY_SYM     ( 7*8 | 1 )
#define HAL_KEY_M       ( 7*8 | 2 )
#define HAL_KEY_N       ( 7*8 | 3 )
#define HAL_KEY_B       ( 7*8 | 4 )

/*
 * Cursor keys: CAPS SHIFT + digit (composite — encoded as values >= 64
 * and handled specially in hal_btn / hal_btnp / hal_btnr).
 *   LEFT  = CAPS + 5   RIGHT = CAPS + 8
 *   UP    = CAPS + 7   DOWN  = CAPS + 6
 */
#define HAL_KEY_LEFT    64
#define HAL_KEY_RIGHT   65
#define HAL_KEY_UP      66
#define HAL_KEY_DOWN    67

/* ── Aliases para teclas sin equivalente directo en ZX ───────────────────── */
#define HAL_KEY_ESCAPE    HAL_KEY_SPACE   /* no Escape: SPACE como fallback */
#define HAL_KEY_BACKSPACE HAL_KEY_SHIFT   /* CAPS SHIFT actúa de borrar     */
#define HAL_KEY_TAB       HAL_KEY_SYM    /* no Tab                          */

/* ── Gamepad emulado con cursor keys + Z/X ───────────────────────────────── */
#define HAL_GP1_UP    HAL_KEY_UP
#define HAL_GP1_DOWN  HAL_KEY_DOWN
#define HAL_GP1_LEFT  HAL_KEY_LEFT
#define HAL_GP1_RIGHT HAL_KEY_RIGHT
#define HAL_GP1_A     HAL_KEY_Z
#define HAL_GP1_B     HAL_KEY_X

#endif /* ZX_INPUT_KEYS_H */
