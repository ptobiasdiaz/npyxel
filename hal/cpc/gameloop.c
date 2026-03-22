/*
 * hal/cpc/gameloop.c — System functions for Amstrad CPC 464.
 *
 * Frame sync: Gate Array generates a VSYNC interrupt every ~20ms (50 Hz).
 * hal_flip() is called once per frame by the generated main() immediately
 * after the HALT instruction (which waits for the next interrupt).
 *
 * Gate Array commands (port 0x7FFF, write only):
 *   bits 7-6 = 0b10: mode + ROM control
 *     bits 1-0: video mode (0=Mode0, 1=Mode1, 2=Mode2)
 *     bit 2:    lower ROM disable
 *     bit 3:    upper ROM disable
 *   bits 7-6 = 0b00: select pen  (bit4=1 → border, bits3-0 = pen 0-15)
 *   bits 7-6 = 0b01: set color   (bits4-0 = hardware color 0-31)
 *
 * Pyxel color → CPC hardware palette mapping defined in graphics.c.
 *
 * Compile with:  zcc +cpc
 */

#include <string.h>
#include "hal/hal.h"
#include "hal/cpc/input_keys.h"

/* ── Internal state ──────────────────────────────────────────────────────── */

static unsigned int _frame_count;

/* Keyboard state: 10 lines × 8 bits (0 = pressed, active low) */
unsigned char _cpc_keys_curr[10];
unsigned char _cpc_keys_prev[10];

/* ── Hardware access ─────────────────────────────────────────────────────── */

extern void         outp(unsigned int port, unsigned char value);
extern unsigned char inp(unsigned int port);

/* Gate Array port */
#define GA_PORT     0x7FFFu

/* PPI ports (standard CPC addresses) */
#define PPI_PORT_A  0xF4FFu   /* read: keyboard / PSG data */
#define PPI_PORT_C  0xF6FFu   /* write: PSG control + keyboard line select */

/* ── Palette setup ───────────────────────────────────────────────────────── */

static const unsigned char _pyxel_to_cpc_hw[16] = {
    20,  4,  5,  2, 28, 16, 31,  0,
    12, 14, 10, 25, 23, 22, 15,  3,
};

static void _setup_palette(void)
{
    int pen;
    /* Border = black */
    outp(GA_PORT, (unsigned char)(0x10u));           /* select border */
    outp(GA_PORT, (unsigned char)(0x40u | 20u));     /* hw color 20 = black */

    for (pen = 0; pen < 16; pen++) {
        outp(GA_PORT, (unsigned char)(0x00u | (unsigned int)pen));
        outp(GA_PORT, (unsigned char)(0x40u | _pyxel_to_cpc_hw[pen]));
    }
}

/* ── Keyboard scan ───────────────────────────────────────────────────────── */

static void _scan_keyboard(unsigned char *buf)
{
    int line;
    /*
     * For each of the 10 keyboard lines:
     *   1. Write line number to PPI Port C (bits 3-0 = line, bits 7-6 = PSG read mode)
     *   2. Read PPI Port A to get 8-bit key state (0 = pressed)
     *
     * PSG mode bits in Port C upper nibble:
     *   0b01xxxxxx = BDIR=0, BC1=1 → PSG read data
     * The PSG must already have register 14 (Port A) selected — the CPC
     * firmware does this during startup.
     */
    for (line = 0; line < 10; line++) {
        /* PSG must be inactive (bits 7-6 = 00) so Port A acts as input */
        outp(PPI_PORT_C, (unsigned char)(unsigned int)line);
        buf[line] = inp(PPI_PORT_A);
    }
}

/* ── hal_init ────────────────────────────────────────────────────────────── */

void hal_init(void)
{
    _frame_count = 0u;

    /* Set Mode 0, both ROMs enabled */
    outp(GA_PORT, (unsigned char)(0x80u | 0x00u));

    _setup_palette();

    _scan_keyboard(_cpc_keys_curr);
    memcpy(_cpc_keys_prev, _cpc_keys_curr, 10);

    hal_cls(0);
}

/* ── hal_quit ────────────────────────────────────────────────────────────── */

void hal_quit(void)
{
    /* Soft reset via RST 0 — returns to CPC firmware/BASIC */
    __asm__("RST 0x00");
}

/* ── hal_flip ────────────────────────────────────────────────────────────── */

void hal_flip(void)
{
    _frame_count++;
    memcpy(_cpc_keys_prev, _cpc_keys_curr, 10);
    _scan_keyboard(_cpc_keys_curr);
}

/* ── hal_frame_count ─────────────────────────────────────────────────────── */

unsigned int hal_frame_count(void)
{
    return _frame_count;
}

/* ── hal_wait_cycles ─────────────────────────────────────────────────────── */

void hal_wait_cycles(unsigned int cycles)
{
    volatile unsigned int i;
    /* CPC Z80 at 4 MHz; ~4 T-states per iteration */
    for (i = 0u; i < (cycles >> 2); i++) { }
}

/* ── hal_debug_print ─────────────────────────────────────────────────────── */

void hal_debug_print(const char *s)
{
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
