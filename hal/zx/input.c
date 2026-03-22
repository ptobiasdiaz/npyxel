/*
 * hal/zx/input.c — ZX Spectrum 48K keyboard input.
 *
 * Keyboard state is maintained by gameloop.c (hal_flip snapshots it).
 * This file provides the hal_btn / hal_btnp / hal_btnr interface.
 *
 * Key encoding (from input_keys.h):
 *   Normal keys: (row << 3) | bit   — row 0-7, bit 0-4
 *   Cursor keys: 64-67             — composite (CAPS SHIFT + digit)
 *
 * Bit is 0 when pressed (active low); we return 1 for "pressed".
 *
 * Compile with:  zcc +zx
 */

#include "hal/hal.h"
#include "hal/zx/input_keys.h"

/* Keyboard snapshots maintained by gameloop.c */
extern unsigned char _zx_keys_curr[8];
extern unsigned char _zx_keys_prev[8];

/* ── Internal helpers ────────────────────────────────────────────────────── */

/*
 * Returns 1 if a normal key (code < 64) is pressed in the given snapshot.
 * bit = 0 means pressed (active low).
 */
static int _key_in_buf(int key, const unsigned char *buf)
{
    int row = key >> 3;
    int bit = key & 7;
    if (row < 0 || row > 7 || bit > 4) return 0;
    return !(buf[row] & (unsigned char)(1u << (unsigned int)bit));
}

/*
 * Cursor keys = CAPS SHIFT (row 0 bit 0) held simultaneously with a digit.
 *   LEFT  = CAPS + 5  (row 3 bit 4)
 *   RIGHT = CAPS + 8  (row 4 bit 2)
 *   UP    = CAPS + 7  (row 4 bit 3)
 *   DOWN  = CAPS + 6  (row 4 bit 4)
 */
static int _cursor_in_buf(int key, const unsigned char *buf)
{
    int caps = !(buf[0] & 0x01u);  /* CAPS SHIFT pressed? */
    if (!caps) return 0;
    switch (key) {
        case HAL_KEY_LEFT:  return !(buf[3] & 0x10u);  /* 5 */
        case HAL_KEY_RIGHT: return !(buf[4] & 0x04u);  /* 8 */
        case HAL_KEY_UP:    return !(buf[4] & 0x08u);  /* 7 */
        case HAL_KEY_DOWN:  return !(buf[4] & 0x10u);  /* 6 */
        default:            return 0;
    }
}

static int _is_down(int key, const unsigned char *buf)
{
    if (key < 0)   return 0;
    if (key >= 64) return _cursor_in_buf(key, buf);
    return _key_in_buf(key, buf);
}

/* ── hal_btn ─────────────────────────────────────────────────────────────── */

int hal_btn(int key)
{
    return _is_down(key, _zx_keys_curr);
}

/* ── hal_btnp ────────────────────────────────────────────────────────────── */
/*
 * Returns 1 on the frame the key is first pressed.
 * Auto-repeat: after `hold` frames, fires every `period` frames.
 * Simplified: hold/period = 0 → just detect first press.
 */
int hal_btnp(int key, int hold, int period)
{
    int curr = _is_down(key, _zx_keys_curr);
    int prev = _is_down(key, _zx_keys_prev);

    if (!curr) return 0;
    if (!prev) return 1;    /* first frame down */

    /* Auto-repeat (basic implementation) */
    if (hold > 0 && period > 0) {
        unsigned int fc = hal_frame_count();
        if (fc > (unsigned int)hold &&
            ((fc - (unsigned int)hold) % (unsigned int)period) == 0u)
            return 1;
    }
    return 0;
}

/* ── hal_btnr ────────────────────────────────────────────────────────────── */

int hal_btnr(int key)
{
    return !_is_down(key, _zx_keys_curr) && _is_down(key, _zx_keys_prev);
}
