/*
 * hal/common/bresenham.c — Portable drawing primitives for pyxel-retro.
 *
 * All functions call hal_pset() and are target-independent.
 * Each target can override individual functions with optimized versions.
 *
 * Algorithms:
 *   hal_line   — Bresenham's line
 *   hal_rectb  — rectangle outline (4 lines)
 *   hal_circ   — filled circle (Midpoint / Bresenham circle)
 *   hal_circb  — circle outline
 *   hal_elli   — filled ellipse (integer parametric)
 *   hal_ellib  — ellipse outline
 *   hal_tri    — filled triangle (scanline)
 *   hal_trib   — triangle outline (3 lines)
 *   hal_fill   — flood fill (iterative stack, no system stack)
 *
 * C89 compliant.  No stdlib beyond <string.h> for fill stack.
 */

#include <string.h>
#include "hal/hal.h"

/* ── hal_line (Bresenham) ────────────────────────────────────────────────── */

void hal_line(int x0, int y0, int x1, int y1, int col)
{
    int dx, dy, sx, sy, err, e2;

    dx  = (x1 > x0) ? (x1 - x0) : (x0 - x1);
    dy  = (y1 > y0) ? (y1 - y0) : (y0 - y1);
    sx  = (x0 < x1) ? 1 : -1;
    sy  = (y0 < y1) ? 1 : -1;
    err = dx - dy;

    for (;;) {
        hal_pset(x0, y0, col);
        if (x0 == x1 && y0 == y1) break;
        e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 <  dx) { err += dx; y0 += sy; }
    }
}

/* ── hal_rectb (outline) ─────────────────────────────────────────────────── */

void hal_rectb(int x, int y, int w, int h, int col)
{
    hal_line(x,         y,         x + w - 1, y,         col);
    hal_line(x,         y + h - 1, x + w - 1, y + h - 1, col);
    hal_line(x,         y,         x,         y + h - 1, col);
    hal_line(x + w - 1, y,         x + w - 1, y + h - 1, col);
}

/* ── hal_circb (outline, Midpoint circle) ────────────────────────────────── */

void hal_circb(int cx, int cy, int r, int col)
{
    int x = 0, y = r, d = 3 - 2 * r;
    while (y >= x) {
        hal_pset(cx + x, cy + y, col);
        hal_pset(cx - x, cy + y, col);
        hal_pset(cx + x, cy - y, col);
        hal_pset(cx - x, cy - y, col);
        hal_pset(cx + y, cy + x, col);
        hal_pset(cx - y, cy + x, col);
        hal_pset(cx + y, cy - x, col);
        hal_pset(cx - y, cy - x, col);
        if (d < 0) {
            d += 4 * x + 6;
        } else {
            d += 4 * (x - y) + 10;
            y--;
        }
        x++;
    }
}

/* ── hal_circ (filled) ───────────────────────────────────────────────────── */

void hal_circ(int cx, int cy, int r, int col)
{
    int x = 0, y = r, d = 3 - 2 * r;
    int i;
    while (y >= x) {
        for (i = cx - x; i <= cx + x; i++) {
            hal_pset(i, cy + y, col);
            hal_pset(i, cy - y, col);
        }
        for (i = cx - y; i <= cx + y; i++) {
            hal_pset(i, cy + x, col);
            hal_pset(i, cy - x, col);
        }
        if (d < 0) {
            d += 4 * x + 6;
        } else {
            d += 4 * (x - y) + 10;
            y--;
        }
        x++;
    }
}

/* ── hal_ellib (ellipse outline, integer parametric) ─────────────────────── */
/*
 * Plots 4 symmetric quadrant points as the parameter sweeps one quadrant.
 * Uses integer arithmetic: dx² + dy² ≈ r² only at axis points, but the
 * midpoint approach is accurate enough for retro use.
 */
void hal_ellib(int cx, int cy, int a, int b, int col)
{
    /* Midpoint ellipse algorithm */
    long a2 = (long)a * a;
    long b2 = (long)b * b;
    long fa2 = 4L * a2;
    long fb2 = 4L * b2;
    long x, y, sigma;

    /* Region 1 */
    x = 0; y = b;
    sigma = (long)(2 * b2) + a2 * (long)(1 - 2 * b);
    while (b2 * x <= a2 * y) {
        hal_pset((int)(cx + x), (int)(cy + y), col);
        hal_pset((int)(cx - x), (int)(cy + y), col);
        hal_pset((int)(cx + x), (int)(cy - y), col);
        hal_pset((int)(cx - x), (int)(cy - y), col);
        if (sigma >= 0) { sigma += fa2 * (1L - y); y--; }
        sigma += b2 * (4L * x + 6L);
        x++;
    }

    /* Region 2 */
    x = a; y = 0;
    sigma = (long)(2 * a2) + b2 * (long)(1 - 2 * a);
    while (a2 * y <= b2 * x) {
        hal_pset((int)(cx + x), (int)(cy + y), col);
        hal_pset((int)(cx - x), (int)(cy + y), col);
        hal_pset((int)(cx + x), (int)(cy - y), col);
        hal_pset((int)(cx - x), (int)(cy - y), col);
        if (sigma >= 0) { sigma += fb2 * (1L - x); x--; }
        sigma += a2 * (4L * y + 6L);
        y++;
    }
}

/* ── hal_elli (filled ellipse) ───────────────────────────────────────────── */

void hal_elli(int cx, int cy, int a, int b, int col)
{
    int x, y;
    long a2 = (long)a * a;
    long b2 = (long)b * b;
    for (y = -b; y <= b; y++) {
        /* x range: a * sqrt(1 - y²/b²) — use integer: x² ≤ a²(1 - y²/b²) */
        /* x_max = a * sqrt((b² - y²) / b²) → x_max² = a²(b² - y²)/b² */
        long y2 = (long)y * y;
        if (y2 > b2) continue;
        /* x_max = a * sqrt(b2 - y2) / b — integer approx */
        /* To avoid sqrt: iterate x or use precomputed width */
        long xw2 = a2 * (b2 - y2);   /* = (a*x_max)² * b² → need x_max */
        /* Binary search or direct: since b is small on 8-bit, scan is OK */
        for (x = 0; (long)x * x * b2 <= xw2; x++) {}
        x--;
        hal_line(cx - x, cy + y, cx + x, cy + y, col);
    }
}

/* ── hal_trib (triangle outline) ─────────────────────────────────────────── */

void hal_trib(int x1, int y1, int x2, int y2, int x3, int y3, int col)
{
    hal_line(x1, y1, x2, y2, col);
    hal_line(x2, y2, x3, y3, col);
    hal_line(x3, y3, x1, y1, col);
}

/* ── hal_tri (filled triangle, scanline) ─────────────────────────────────── */

static void _swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

void hal_tri(int x1, int y1, int x2, int y2, int x3, int y3, int col)
{
    int y, xa, xb;
    /* Sort vertices by y */
    if (y1 > y2) { _swap(&x1,&x2); _swap(&y1,&y2); }
    if (y1 > y3) { _swap(&x1,&x3); _swap(&y1,&y3); }
    if (y2 > y3) { _swap(&x2,&x3); _swap(&y2,&y3); }

    /* Flat-bottom triangle (y1..y2) */
    if (y2 != y1) {
        for (y = y1; y <= y2; y++) {
            xa = x1 + (x2 - x1) * (y - y1) / (y2 - y1);
            xb = x1 + (x3 - x1) * (y - y1) / (y3 - y1);
            if (xa > xb) _swap(&xa, &xb);
            hal_line(xa, y, xb, y, col);
        }
    }
    /* Flat-top triangle (y2..y3) */
    if (y3 != y2) {
        for (y = y2; y <= y3; y++) {
            xa = x2 + (x3 - x2) * (y - y2) / (y3 - y2);
            xb = x1 + (x3 - x1) * (y - y1) / (y3 - y1);
            if (xa > xb) _swap(&xa, &xb);
            hal_line(xa, y, xb, y, col);
        }
    }
}

/* ── hal_fill (iterative flood fill) ─────────────────────────────────────── */
/*
 * 8-bit machines have very limited stack.  We use a fixed-size array as
 * an explicit LIFO stack instead of recursion.
 * Stack size 512 entries × 4 bytes = 2 KB — acceptable for ZX 48K.
 */

#define FILL_STACK_SIZE 512

typedef struct { short x; short y; } FillEntry;
static FillEntry _fill_stack[FILL_STACK_SIZE];

void hal_fill(int x, int y, int col)
{
    int top = 0;
    int target = hal_pget(x, y);
    FillEntry e;
    int cx, cy;

    if (target == col) return;

    _fill_stack[top].x = (short)x;
    _fill_stack[top].y = (short)y;
    top++;

    while (top > 0) {
        top--;
        e  = _fill_stack[top];
        cx = (int)e.x;
        cy = (int)e.y;

        if (cx < 0 || cx >= 256 || cy < 0 || cy >= 192) continue;
        if (hal_pget(cx, cy) != target) continue;

        hal_pset(cx, cy, col);

#define PUSH(nx, ny) \
        if (top < FILL_STACK_SIZE) { \
            _fill_stack[top].x = (short)(nx); \
            _fill_stack[top].y = (short)(ny); \
            top++; \
        }

        PUSH(cx + 1, cy);
        PUSH(cx - 1, cy);
        PUSH(cx, cy + 1);
        PUSH(cx, cy - 1);
#undef PUSH
    }
}
