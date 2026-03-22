/*
 * hal/cpc/input_keys.h — Amstrad CPC 464 keyboard matrix constants.
 *
 * Matrix: 10 lines × 8 bits.  Bit = 0 means PRESSED (active low).
 * Key encoding:  (line * 8) + bit
 *
 * Source: /home/tobias/dev/multiemu/frontend/keymap.py (CPC_PYGAME_KEYMAP)
 * Hardware read: PPI Port C bits 3-0 select line, PPI Port A reads bits 7-0.
 *
 *       bit7   bit6   bit5   bit4   bit3   bit2   bit1   bit0
 * L0    -      -      -      -      DOWN   UP     RIGHT  (KPEnter l6)
 * L1    LEFT   -      -      -      -      -      -      -
 * L2    CTRL   BSLASH SHIFT  -      RBKRT  RETURN LBRKT  -
 * L3    PERIOD -      -      SLASH  SEMI   P      MINUS  -
 * L4    COMMA  M      K      L      I      O      9      0
 * L5    SPACE  N      J      H      Y      U      7      8
 * L6    V      B      F      G      T      R      5      6
 * L7    X      C      D      S      W      E      3      4
 * L8    Z      CAPS   A      TAB    Q      ESC    2      1
 * L9    DEL    KP.    -      -      -      -      -      -
 */

#ifndef CPC_INPUT_KEYS_H
#define CPC_INPUT_KEYS_H

/* ── Line 0 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_UP      (0*8 + 0)
#define HAL_KEY_RIGHT   (0*8 + 1)
#define HAL_KEY_DOWN    (0*8 + 2)
/* bit 3-5: unused */
#define HAL_KEY_RETURN  (0*8 + 6)   /* numeric keypad Enter → main Enter */

/* ── Line 1 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_LEFT    (1*8 + 0)

/* ── Line 2 ──────────────────────────────────────────────────────────────── */
/* bit 0: unused */
#define HAL_KEY_LBRKT   (2*8 + 1)   /* [ { */
#define HAL_KEY_RETURN2 (2*8 + 2)   /* main keyboard Return */
#define HAL_KEY_RBRKT   (2*8 + 3)   /* ] } */
/* bit 4: unused */
#define HAL_KEY_SHIFT   (2*8 + 5)
#define HAL_KEY_BACKSLASH (2*8 + 6)
#define HAL_KEY_CTRL    (2*8 + 7)

/* ── Line 3 ──────────────────────────────────────────────────────────────── */
/* bit 0: unused */
#define HAL_KEY_MINUS   (3*8 + 1)
#define HAL_KEY_P       (3*8 + 3)
#define HAL_KEY_SEMICOL (3*8 + 4)
#define HAL_KEY_SLASH   (3*8 + 6)
#define HAL_KEY_PERIOD  (3*8 + 7)

/* ── Line 4 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_0       (4*8 + 0)
#define HAL_KEY_9       (4*8 + 1)
#define HAL_KEY_O       (4*8 + 2)
#define HAL_KEY_I       (4*8 + 3)
#define HAL_KEY_L       (4*8 + 4)
#define HAL_KEY_K       (4*8 + 5)
#define HAL_KEY_M       (4*8 + 6)
#define HAL_KEY_COMMA   (4*8 + 7)

/* ── Line 5 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_8       (5*8 + 0)
#define HAL_KEY_7       (5*8 + 1)
#define HAL_KEY_U       (5*8 + 2)
#define HAL_KEY_Y       (5*8 + 3)
#define HAL_KEY_H       (5*8 + 4)
#define HAL_KEY_J       (5*8 + 5)
#define HAL_KEY_N       (5*8 + 6)
#define HAL_KEY_SPACE   (5*8 + 7)

/* ── Line 6 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_6       (6*8 + 0)
#define HAL_KEY_5       (6*8 + 1)
#define HAL_KEY_R       (6*8 + 2)
#define HAL_KEY_T       (6*8 + 3)
#define HAL_KEY_G       (6*8 + 4)
#define HAL_KEY_F       (6*8 + 5)
#define HAL_KEY_B       (6*8 + 6)
#define HAL_KEY_V       (6*8 + 7)

/* ── Line 7 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_4       (7*8 + 0)
#define HAL_KEY_3       (7*8 + 1)
#define HAL_KEY_E       (7*8 + 2)
#define HAL_KEY_W       (7*8 + 3)
#define HAL_KEY_S       (7*8 + 4)
#define HAL_KEY_D       (7*8 + 5)
#define HAL_KEY_C       (7*8 + 6)
#define HAL_KEY_X       (7*8 + 7)

/* ── Line 8 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_1       (8*8 + 0)
#define HAL_KEY_2       (8*8 + 1)
#define HAL_KEY_ESCAPE  (8*8 + 2)
#define HAL_KEY_Q       (8*8 + 3)
#define HAL_KEY_TAB     (8*8 + 4)
#define HAL_KEY_A       (8*8 + 5)
#define HAL_KEY_CAPS    (8*8 + 6)
#define HAL_KEY_Z       (8*8 + 7)

/* ── Line 9 ──────────────────────────────────────────────────────────────── */
#define HAL_KEY_BACKSPACE (9*8 + 7)   /* DEL on CPC = backspace */

/* ── Aliases ─────────────────────────────────────────────────────────────── */
/* Letters not yet defined (complete A-Z) */
#define HAL_KEY_LSHIFT  HAL_KEY_SHIFT
#define HAL_KEY_RSHIFT  HAL_KEY_SHIFT

/* ── Gamepad emulated with cursor keys + Z/X ─────────────────────────────── */
#define HAL_GP1_UP    HAL_KEY_UP
#define HAL_GP1_DOWN  HAL_KEY_DOWN
#define HAL_GP1_LEFT  HAL_KEY_LEFT
#define HAL_GP1_RIGHT HAL_KEY_RIGHT
#define HAL_GP1_A     HAL_KEY_Z
#define HAL_GP1_B     HAL_KEY_X

#endif /* CPC_INPUT_KEYS_H */
