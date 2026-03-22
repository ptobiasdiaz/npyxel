/*
 * hal/cpc/sound.c — Amstrad CPC 464 AY-3-8912 sound (stubs).
 *
 * The AY-3-8912 is accessed via PPI Port A (data) and Port C upper nibble
 * (PSG control: BDIR/BC1).  Register write sequence:
 *   1. Latch register address: Port C = 0xC0|reg, Port A = reg_num, deactivate
 *   2. Write value:            Port C = 0x80|x,   Port A = value,   deactivate
 *
 * Key AY registers:
 *   0-1: Channel A tone period (low/high)
 *   2-3: Channel B tone period
 *   4-5: Channel C tone period
 *   6:   Noise period
 *   7:   Mixer (enable bits, active low; bits 6-3 = port I/O)
 *   8-10: Channel amplitude (bit4=use envelope, bits3-0=level)
 *   11-12: Envelope period
 *   13:  Envelope shape
 *   14:  Port A (keyboard input — do not write in keyboard mode)
 *
 * Compile with:  zcc +cpc
 */

#include "hal/hal.h"
#include "hal/cpc/input_keys.h"

extern void          outp(unsigned int port, unsigned char value);
extern unsigned char inp(unsigned int port);

#define PPI_PORT_A  0xF4FFu
#define PPI_PORT_C  0xF6FFu

/* ── AY register write ───────────────────────────────────────────────────── */

static void _ay_write(unsigned char reg, unsigned char val)
{
    /* Latch register address */
    outp(PPI_PORT_C, 0xC0u);
    outp(PPI_PORT_A, reg);
    outp(PPI_PORT_C, 0x00u);

    /* Write value */
    outp(PPI_PORT_C, 0x80u);
    outp(PPI_PORT_A, val);
    outp(PPI_PORT_C, 0x00u);
}

/* ── hal_play (stub — plays a short beep) ───────────────────────────────── */

void hal_play(int ch, int snd, int loop)
{
    (void)snd; (void)loop;
    /* Very rough: enable channel A tone, set a mid frequency, then silence */
    _ay_write(7, 0x3E);    /* enable channel A tone (bit 0 = 0 = on) */
    _ay_write(0, 200);     /* tone period low byte */
    _ay_write(1, 0);       /* tone period high byte */
    _ay_write(8, 12);      /* channel A amplitude = 12 */
    (void)ch;
    /* TODO: use asset sound data and duration */
}

/* ── hal_playm / hal_stop / hal_play_pos (stubs) ───────────────────────── */

void hal_playm(int msc, int loop) { (void)msc; (void)loop; }

void hal_stop(int ch)
{
    (void)ch;
    /* Silence all channels */
    _ay_write(8, 0);
    _ay_write(9, 0);
    _ay_write(10, 0);
    _ay_write(7, 0x3F);    /* disable all tones and noise */
}

int hal_play_pos(int ch) { (void)ch; return -1; }
