/*
 * hal/common/strconv.c — Portable integer-to-string conversion.
 *
 * hal_istr(n) converts an int to a decimal string stored in a static buffer.
 * Handles negative numbers.  Buffer is overwritten on each call.
 *
 * C89 compliant.  No stdlib required.
 */

#include "hal/hal.h"

const char *hal_istr(int n)
{
    static char buf[12];   /* "-2147483648\0" = 12 chars max */
    char *p = buf + 11;
    int neg = 0;

    *p = '\0';

    if (n < 0) {
        neg = 1;
        /* Avoid overflow on INT_MIN: negate digit by digit */
        do {
            *--p = (char)('0' - (n % 10));
            n /= 10;
        } while (n != 0);
        *--p = '-';
    } else {
        do {
            *--p = (char)('0' + (n % 10));
            n /= 10;
        } while (n != 0);
    }

    (void)neg;   /* used only for the sign branch above */
    return p;
}
