/*
 * hal/zx/gameloop.c — System functions for ZX Spectrum 48K.
 *
 * Game loop sync: HALT instruction waits for the ULA interrupt (~50 Hz PAL).
 * hal_flip() is called once per frame by the generated main() to update
 * the frame counter and snapshot the keyboard state for btnp/btnr.
 *
 * Compile with:  zcc +zx
 */

#include <string.h>
#include "hal/hal.h"
#include "hal/zx/input_keys.h"

/* ── Internal state ──────────────────────────────────────────────────────── */

static unsigned int  _frame_count;

/* Keyboard state: 8 half-rows, 5 bits each (0 = pressed, active low) */
/* Exposed to input.c via external declaration */
unsigned char _zx_keys_curr[8];
unsigned char _zx_keys_prev[8];

/* Half-row port addresses (high byte varies, low byte = 0xFE) */
static const unsigned int _zx_ports[8] = {
    0xFEFEu, 0xFDFEu, 0xFBFEu, 0xF7FEu,
    0xEFFEu, 0xDFFEu, 0xBFFEu, 0x7FFEu
};

/* z88dk port input: reads a byte from an I/O port */
extern unsigned char inp(unsigned int port);

static void _scan_keyboard(unsigned char *buf)
{
    int i;
    for (i = 0; i < 8; i++) {
        buf[i] = (unsigned char)(inp(_zx_ports[i]) & 0x1Fu);
    }
}

/* ── hal_init ────────────────────────────────────────────────────────────── */

void hal_init(void)
{
    _frame_count = 0u;
    _scan_keyboard(_zx_keys_curr);
    memcpy(_zx_keys_prev, _zx_keys_curr, 8);
    hal_cls(0);
}

/* ── hal_quit ────────────────────────────────────────────────────────────── */

void hal_quit(void)
{
    /* Jump to ROM restart — returns to BASIC */
    __asm__("RST 0x00");
}

/* ── hal_flip ────────────────────────────────────────────────────────────── */
/*
 * Called once per frame (after HALT in the main loop).
 * Updates frame counter and snapshots keyboard for btnp/btnr.
 */
void hal_flip(void)
{
    _frame_count++;
    memcpy(_zx_keys_prev, _zx_keys_curr, 8);
    _scan_keyboard(_zx_keys_curr);
}

/* ── hal_frame_count ─────────────────────────────────────────────────────── */

unsigned int hal_frame_count(void)
{
    return _frame_count;
}

/* ── hal_wait_cycles ─────────────────────────────────────────────────────── */

void hal_wait_cycles(unsigned int cycles)
{
    /* Busy-wait approximation: each iteration ≈ 13 T-states at 3.5 MHz */
    volatile unsigned int i;
    for (i = 0; i < (cycles / 13u); i++) {
        /* nothing */
    }
}

/* ── hal_debug_print ─────────────────────────────────────────────────────── */

void hal_debug_print(const char *s)
{
    /* Stub: would use ROM PRINT (RST 0x10) or BDOS equivalent */
    (void)s;
}

/* ── hal_ipow ────────────────────────────────────────────────────────────── */

int hal_ipow(int base, int exp)
{
    int result = 1;
    while (exp > 0) {
        if (exp & 1) result *= base;
        base *= base;
        exp >>= 1;
    }
    return result;
}
