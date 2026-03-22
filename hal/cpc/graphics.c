/*
 * hal/cpc/graphics.c — Amstrad CPC 464 graphics (Gate Array Mode 0).
 *
 * Mode 0: 160×200, 16 colors, 2 pixels per byte (4 bits each).
 * Screen RAM default base: 0xC000 (CRTC start MA = 0x3000).
 *
 * Pixel address formula (from CRTC MA mapping):
 *   ma        = CPC_SCREEN_MA + (y >> 3) * 40 + (x >> 2)
 *   base_addr = (((ma & 0x3000) << 2) | ((raster & 7) << 11) | ((ma & 0x3FF) << 1))
 *   byte_addr = base_addr + ((x >> 1) & 1)
 *   pixel_sel = x & 1        (0 = left pixel, 1 = right pixel)
 *
 * Mode 0 pixel encoding (4 bits → bits of byte):
 *   Left  pixel (sel=0): bits 7,5,3,1  mask=0xAA
 *   Right pixel (sel=1): bits 6,4,2,0  mask=0x55
 *
 * Compile with:  zcc +cpc
 */

#include <string.h>
#include "hal/hal.h"
#include "hal/cpc/input_keys.h"
#include "hal/common/font_8x8.h"

/* ── Screen constants ────────────────────────────────────────────────────── */

#define CPC_SCREEN_MA    0x3000u    /* CRTC display start address */
#define CPC_SCREEN_BASE  0xC000u    /* Physical RAM address */
#define CPC_SCREEN_W     160
#define CPC_SCREEN_H     200

/* ── Gate Array port ─────────────────────────────────────────────────────── */
#define GA_PORT   0x7FFFu

extern void outp(unsigned int port, unsigned char value);

/* ── Pyxel color (0-15) → CPC hardware palette index (0-31) ─────────────── */
/*
 * CPC hardware palette (from multiemu cpc_gate_array_accel.pyx):
 *   20=Black, 0=White, 12=Red, 18=Green, 21=Blue, 6=Cyan, 13=Magenta,
 *   10=Yellow, 14=Orange, 22=DarkGreen, 4=DarkBlue, 2=SeaGreen, ...
 */
static const unsigned char _pyxel_to_cpc_hw[16] = {
    20, /*  0 Black       → hw 20 (0,0,0)          */
     4, /*  1 Dark Navy   → hw  4 (0,0,128)         */
     5, /*  2 Purple      → hw  5 (128,0,128)       */
     2, /*  3 Teal        → hw  2 (0,128,128)       */
    28, /*  4 Brown       → hw 28 (128,0,0)         */
    16, /*  5 Dark Blue   → hw 16 (0,0,128)         */
    31, /*  6 Lavender    → hw 31 (128,128,255)     */
     0, /*  7 White       → hw  0 (255,255,255)     */
    12, /*  8 Red         → hw 12 (255,0,0)         */
    14, /*  9 Orange      → hw 14 (255,128,0)       */
    10, /* 10 Yellow      → hw 10 (255,255,0)       */
    25, /* 11 Lt Green    → hw 25 (128,255,128)     */
    23, /* 12 Sky Blue    → hw 23 (128,192,255)     */
    22, /* 13 Gray        → hw 22 (0,128,0) approx  */
    15, /* 14 Pink        → hw 15 (255,128,255)     */
     3, /* 15 Cream       → hw  3 (255,255,128)     */
};

/* ── Mode 0 pixel encode/decode ──────────────────────────────────────────── */

/*
 * Mode 0 byte layout (CPC Technical Reference):
 *   bit 7 = left  pixel color bit 0    bit 6 = right pixel color bit 0
 *   bit 5 = left  pixel color bit 1    bit 4 = right pixel color bit 1
 *   bit 3 = left  pixel color bit 2    bit 2 = right pixel color bit 2
 *   bit 1 = left  pixel color bit 3    bit 0 = right pixel color bit 3
 */
static unsigned char _encode_left(int pen)
{
    return (unsigned char)(
        ((pen & 1)        << 7) |
        (((pen >> 1) & 1) << 5) |
        (((pen >> 2) & 1) << 3) |
        (((pen >> 3) & 1) << 1)
    );
}

static unsigned char _encode_right(int pen)
{
    return (unsigned char)(
        ((pen & 1)        << 6) |
        (((pen >> 1) & 1) << 4) |
        (((pen >> 2) & 1) << 2) |
        (((pen >> 3) & 1) << 0)
    );
}

static int _decode_left(unsigned char byte)
{
    return (int)(
        ((byte >> 7) & 1)        |
        (((byte >> 5) & 1) << 1) |
        (((byte >> 3) & 1) << 2) |
        (((byte >> 1) & 1) << 3)
    );
}

static int _decode_right(unsigned char byte)
{
    return (int)(
        ((byte >> 6) & 1)        |
        (((byte >> 4) & 1) << 1) |
        (((byte >> 2) & 1) << 2) |
        ((byte & 1)         << 3)
    );
}

/* ── Physical byte address for pixel (x, y) ─────────────────────────────── */

static volatile unsigned char *_pixel_byte(int x, int y)
{
    unsigned int ma      = CPC_SCREEN_MA
                         + (unsigned int)(y >> 3) * 40u
                         + (unsigned int)(x >> 2);
    unsigned int raster  = (unsigned int)(y & 7);
    unsigned int base    = (((ma & 0x3000u) << 2)
                          | (raster << 11)
                          | ((ma & 0x03FFu) << 1));
    return (volatile unsigned char *)(base + (((unsigned int)x >> 1) & 1u));
}

/* ── hal_cls ─────────────────────────────────────────────────────────────── */

void hal_cls(int col)
{
    unsigned char fill;
    int pen = col & 15;

    /* Both pixels in each byte set to the same pen */
    fill = (unsigned char)(_encode_left(pen) | _encode_right(pen));

    /*
     * CPC Mode 0 screen: 25 char rows × 8 rasters × 80 bytes = 16000 bytes.
     * Physical layout is non-linear; fill each raster segment separately.
     */
    {
        unsigned int char_row, raster;
        for (char_row = 0u; char_row < 25u; char_row++) {
            for (raster = 0u; raster < 8u; raster++) {
                unsigned int ma   = CPC_SCREEN_MA + char_row * 40u;
                unsigned int base = (((ma & 0x3000u) << 2)
                                  | (raster << 11)
                                  | ((ma & 0x03FFu) << 1));
                memset((void *)base, fill, 80u);
            }
        }
    }
}

/* ── hal_pset ────────────────────────────────────────────────────────────── */

void hal_pset(int x, int y, int col)
{
    volatile unsigned char *p;
    int pen = col & 15;

    if (x < 0 || x >= CPC_SCREEN_W || y < 0 || y >= CPC_SCREEN_H) return;

    p = _pixel_byte(x, y);
    if (x & 1) {
        *p = (unsigned char)((*p & 0xAAu) | _encode_right(pen));
    } else {
        *p = (unsigned char)((*p & 0x55u) | _encode_left(pen));
    }
}

/* ── hal_pget ────────────────────────────────────────────────────────────── */

int hal_pget(int x, int y)
{
    volatile unsigned char *p;
    if (x < 0 || x >= CPC_SCREEN_W || y < 0 || y >= CPC_SCREEN_H) return 0;
    p = _pixel_byte(x, y);
    return (x & 1) ? _decode_right(*p) : _decode_left(*p);
}

/* ── hal_rect ────────────────────────────────────────────────────────────── */

void hal_rect(int x, int y, int w, int h, int col)
{
    int px, py;
    for (py = y; py < y + h; py++)
        for (px = x; px < x + w; px++)
            hal_pset(px, py, col);
}

/* ── hal_text ────────────────────────────────────────────────────────────── */

void hal_text(int x, int y, const char *s, int col)
{
    int cx = x;
    int row, bit;

    while (*s) {
        unsigned int ch = (unsigned int)(unsigned char)(*s) - 32u;
        if (ch < 96u) {
            for (row = 0; row < 8; row++) {
                unsigned char bits = font_8x8[ch][row];
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

/* ── hal_blt / hal_bltm (stubs) ─────────────────────────────────────────── */

void hal_blt(int x, int y, int img, int u, int v, int w, int h, int colkey)
{
    (void)x; (void)y; (void)img; (void)u; (void)v;
    (void)w; (void)h; (void)colkey;
}

void hal_bltm(int x, int y, int tm, int u, int v, int w, int h, int colkey)
{
    (void)x; (void)y; (void)tm; (void)u; (void)v;
    (void)w; (void)h; (void)colkey;
}
