/*
 * hal/zx/graphics.c — ZX Spectrum 48K ULA graphics implementation.
 *
 * Screen layout:
 *   Pixel RAM  : 0x4000–0x57FF (6144 bytes)  256×192 pixels, non-linear
 *   Attribute  : 0x5800–0x5AFF  (768 bytes)  32×24 cells of 8×8 pixels
 *
 * Attribute byte:  [FLASH | BRIGHT | P2 P1 P0 | I2 I1 I0]
 *   PAPER (bits 5-3) = background color 0-7
 *   INK   (bits 2-0) = foreground color 0-7
 *   BRIGHT (bit 6)   = double-bright palette
 *
 * Pyxel 16 colors → ZX:
 *   Colors 0-7  → direct color index, no BRIGHT
 *   Colors 8-15 → (col - 8) with BRIGHT=1
 *
 * Font: ZX Spectrum 48K ROM at 0x3D00 (96 chars × 8 bytes, ASCII 32–127)
 *
 * Compile with:  zcc +zx
 */

#include <string.h>
#include "hal/hal.h"
#include "hal/zx/input_keys.h"

/* ── Pixel address formula (ZX non-linear layout) ───────────────────────── */
/*
 *  addr = 0x4000
 *       + (y & 0xC0) << 5    ← which third (top/mid/bottom)
 *       + (y & 0x07) << 8    ← pixel row within character row
 *       + (y & 0x38) << 2    ← character row within third
 *       + (x >> 3)           ← byte column
 */
#define ZX_PIXEL_ADDR(x, y) \
    ((volatile unsigned char *)( \
        0x4000u \
        + (((unsigned int)(y) & 0xC0u) << 5) \
        + (((unsigned int)(y) & 0x07u) << 8) \
        + (((unsigned int)(y) & 0x38u) << 2) \
        + ((unsigned int)(x) >> 3) \
    ))

#define ZX_ATTR_ADDR(x, y) \
    ((volatile unsigned char *)( \
        0x5800u + (((unsigned int)(y) >> 3) << 5) + ((unsigned int)(x) >> 3) \
    ))

/* Build ZX attribute byte from a Pyxel color index */
#define ZX_INK(col)    ((unsigned char)((col) & 7))
#define ZX_BRIGHT(col) ((unsigned char)(((col) >= 8) ? 0x40u : 0u))
#define ZX_ATTR_INK(col) ((unsigned char)(ZX_BRIGHT(col) | ZX_INK(col)))

/* ZX Spectrum 48K ROM character set: ASCII 32 to 127, 8 bytes per char */
#define ZX_ROM_FONT ((const unsigned char *)0x3D00u)

/* ── hal_cls ─────────────────────────────────────────────────────────────── */

void hal_cls(int col)
{
    unsigned char attr;

    /* Clear all pixel bits → screen shows PAPER color */
    memset((void *)0x4000u, 0, 6144u);

    /* PAPER = col, INK = 7 (white default), BRIGHT if col >= 8 */
    attr = (unsigned char)(ZX_BRIGHT(col) | ((ZX_INK(col)) << 3) | 7u);
    memset((void *)0x5800u, attr, 768u);
}

/* ── hal_pset ────────────────────────────────────────────────────────────── */

void hal_pset(int x, int y, int col)
{
    volatile unsigned char *pixel;
    volatile unsigned char *attr;

    if (x < 0 || x >= 256 || y < 0 || y >= 192) return;

    pixel = ZX_PIXEL_ADDR(x, y);
    *pixel |= (unsigned char)(0x80u >> ((unsigned int)x & 7u));

    /* Update INK and BRIGHT; preserve FLASH and PAPER */
    attr  = ZX_ATTR_ADDR(x, y);
    *attr = (unsigned char)((*attr & 0xB8u) | ZX_BRIGHT(col) | ZX_INK(col));
}

/* ── hal_pget ────────────────────────────────────────────────────────────── */

int hal_pget(int x, int y)
{
    volatile unsigned char *pixel;
    volatile unsigned char *attr;
    unsigned char attr_val;
    int bright_offset;
    int color_idx;

    if (x < 0 || x >= 256 || y < 0 || y >= 192) return 0;

    pixel    = ZX_PIXEL_ADDR(x, y);
    attr     = ZX_ATTR_ADDR(x, y);
    attr_val = *attr;

    bright_offset = (attr_val & 0x40u) ? 8 : 0;

    if (*pixel & (unsigned char)(0x80u >> ((unsigned int)x & 7u))) {
        color_idx = attr_val & 7;           /* INK */
    } else {
        color_idx = (attr_val >> 3) & 7;    /* PAPER */
    }
    return color_idx + bright_offset;
}

/* ── hal_rect (filled, pixel-by-pixel) ──────────────────────────────────── */

void hal_rect(int x, int y, int w, int h, int col)
{
    int px, py;
    for (py = y; py < y + h; py++)
        for (px = x; px < x + w; px++)
            hal_pset(px, py, col);
}

/* ── hal_text (uses ZX 48K ROM 8×8 font at 0x3D00) ─────────────────────── */

void hal_text(int x, int y, const char *s, int col)
{
    int cx = x;
    int row, bit;

    while (*s) {
        unsigned int ch = (unsigned int)(unsigned char)(*s) - 32u;
        if (ch < 96u) {
            const unsigned char *glyph = ZX_ROM_FONT + ch * 8u;
            for (row = 0; row < 8; row++) {
                unsigned char bits = glyph[row];
                for (bit = 7; bit >= 0; bit--) {
                    if (bits & (unsigned char)(1u << (unsigned int)bit)) {
                        hal_pset(cx + (7 - bit), y + row, col);
                    }
                }
            }
        }
        cx += 8;
        s++;
    }
}

/* ── hal_flip (no-op on ZX — sync is via HALT in main loop) ─────────────── */
/* Frame counter increment lives in gameloop.c                               */

/* ── hal_blt / hal_bltm (stubs — asset baker not yet implemented) ────────── */

void hal_blt(int x, int y, int img, int u, int v, int w, int h, int colkey)
{
    (void)x; (void)y; (void)img; (void)u; (void)v;
    (void)w; (void)h; (void)colkey;
    /* TODO: blit from asset ROM arrays */
}

void hal_bltm(int x, int y, int tm, int u, int v, int w, int h, int colkey)
{
    (void)x; (void)y; (void)tm; (void)u; (void)v;
    (void)w; (void)h; (void)colkey;
    /* TODO: blit tilemap from asset ROM arrays */
}
