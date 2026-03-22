/*
 * hal/cpc/input.c — Amstrad CPC 464 keyboard input.
 *
 * Keyboard snapshots are maintained by gameloop.c (hal_flip scans them).
 * Key encoding: (line * 8) + bit  — see input_keys.h.
 * Bit = 0 means pressed (active low); hal_btn returns 1 for pressed.
 *
 * Compile with:  zcc +cpc
 */

#include "hal/hal.h"
#include "hal/cpc/input_keys.h"

extern unsigned char _cpc_keys_curr[10];
extern unsigned char _cpc_keys_prev[10];

/* ── Internal helpers ────────────────────────────────────────────────────── */

static int _is_down(int key, const unsigned char *buf)
{
    int line, bit;
    if (key < 0 || key >= 80) return 0;
    line = key >> 3;
    bit  = key & 7;
    if (line >= 10) return 0;
    return !(buf[line] & (unsigned char)(1u << (unsigned int)bit));
}

/* ── hal_btn ─────────────────────────────────────────────────────────────── */

int hal_btn(int key)
{
    return _is_down(key, _cpc_keys_curr);
}

/* ── hal_btnp ────────────────────────────────────────────────────────────── */

int hal_btnp(int key, int hold, int period)
{
    int curr = _is_down(key, _cpc_keys_curr);
    int prev = _is_down(key, _cpc_keys_prev);

    if (!curr) return 0;
    if (!prev) return 1;

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
    return !_is_down(key, _cpc_keys_curr) && _is_down(key, _cpc_keys_prev);
}
