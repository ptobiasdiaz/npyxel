/*
 * hal/zx/sound.c — ZX Spectrum 48K beeper sound (stubs + basic tone).
 *
 * The ZX Spectrum has a 1-bit beeper via bit 4 of port 0xFE.
 * Tone generation is done by bit-banging: toggling the port bit at
 * a frequency that matches the desired pitch.  Timing must be
 * cycle-exact, which requires inline or pure ASM for accuracy.
 *
 * This prototype provides stubs so the HAL contract is satisfied.
 * A full implementation would use SDCC inline ASM delay loops.
 *
 * Compile with:  zcc +zx
 */

#include "hal/hal.h"
#include "hal/zx/input_keys.h"

/* z88dk port output */
extern void outp(unsigned int port, unsigned char value);
extern unsigned char inp(unsigned int port);

/* ── Internal beeper state ───────────────────────────────────────────────── */

#define ZX_BEEPER_PORT 0x00FEu   /* low byte 0xFE, high byte = mic mask etc */
#define ZX_BEEPER_BIT  0x10u     /* bit 4 */

static unsigned char _beeper_state = 0u;

/* Toggle the beeper bit once */
static void _beeper_toggle(void)
{
    _beeper_state ^= ZX_BEEPER_BIT;
    outp(ZX_BEEPER_PORT, _beeper_state);
}

/* ── hal_play (stub) ─────────────────────────────────────────────────────── */
/*
 * In a full implementation this would:
 *   1. Decode the sound data from SOUND_N_* asset arrays (from asset baker)
 *   2. Program the beeper toggle rate for the pitch
 *   3. Handle loop flag
 * For the prototype, a short tone is played to confirm the call.
 */
void hal_play(int ch, int snd, int loop)
{
    /* Very basic: a short burst of toggling at a fixed rate */
    volatile unsigned int i, j;
    (void)ch; (void)snd; (void)loop;

    for (j = 0u; j < 100u; j++) {
        _beeper_toggle();
        for (i = 0u; i < 200u; i++) { /* delay */ }
    }
    /* Ensure beeper ends in silent state */
    _beeper_state &= (unsigned char)(~ZX_BEEPER_BIT);
    outp(ZX_BEEPER_PORT, _beeper_state);
}

/* ── hal_playm (stub) ────────────────────────────────────────────────────── */

void hal_playm(int msc, int loop)
{
    (void)msc; (void)loop;
    /* TODO: play music sequence */
}

/* ── hal_stop (stub) ─────────────────────────────────────────────────────── */

void hal_stop(int ch)
{
    (void)ch;
    _beeper_state &= (unsigned char)(~ZX_BEEPER_BIT);
    outp(ZX_BEEPER_PORT, _beeper_state);
}

/* ── hal_play_pos (stub) ─────────────────────────────────────────────────── */

int hal_play_pos(int ch)
{
    (void)ch;
    return -1;  /* not playing */
}
