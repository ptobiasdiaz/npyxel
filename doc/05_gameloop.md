# Generación del game loop

## Tres niveles de control

| Nivel | Mecanismo | Para quién |
|---|---|---|
| Automático | `pyxel.run(update, draw)` | Usuario normal |
| Parametrizado | `@pyxel.config(...)` + `pyxel.run(...)` | Usuario avanzado |
| Total | `pyxel.run_custom(loop)` | Experto que conoce el hardware |

---

## Nivel 1 — Automático

```python
import pyxel

pyxel.init(160, 120)

def update():
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

def draw():
    pyxel.cls(0)
    pyxel.rect(10, 10, 20, 20, 11)

pyxel.run(update, draw)
```

El transpilador detecta `pyxel.run(update, draw)` y genera el game loop estándar
del target. El usuario no necesita saber nada del hardware.

### Código generado para C64

```c
#include "hal/hal.h"
#include "assets_gen.h"

/* funciones generadas desde el script Python */
void update(void);
void draw(void);

static void __fastcall__ vbl_handler(void) {
    update();
    draw();
    /* ACK raster IRQ */
    VIC.irr = 0x01;
}

void main(void) {
    hal_init();
    /* configurar raster IRQ en línea 251 */
    VIC.rasterline = 251;
    VIC.ctrl1     |= 0x80;
    CIA1.icr       = 0x7F;
    irq_set_handler(vbl_handler);
    /* bucle principal vacío — todo ocurre en la IRQ */
    for (;;) {}
}
```

### Código generado para ZX Spectrum

```c
#include "hal/hal.h"

void update(void);
void draw(void);

void main(void) {
    hal_init();
    for (;;) {
        __asm__("HALT");   /* sincroniza a 50Hz (PAL) via interrupción ULA */
        update();
        draw();
    }
}
```

### Código generado para CP/M

```c
#include "hal/hal.h"

#define CYCLES_PER_FRAME 73728U  /* ~4MHz Z80 / 50Hz */

void update(void);
void draw(void);

void main(void) {
    hal_init();
    for (;;) {
        update();
        draw();
        hal_wait_cycles(CYCLES_PER_FRAME);
    }
}
```

---

## Nivel 2 — Parametrizado

El decorador `@pyxel.config` es una **directiva de compilación**. No existe en
runtime ni genera código de decorador Python. El transpilador lo lee durante el
análisis y ajusta el código del game loop generado.

```python
@pyxel.config(
    sync         = "raster",   # "vbl" | "raster" | "cycles" | "halt"
    vbl_line     = 200,        # línea de raster (solo targets con raster IRQ)
    fps          = 50,         # FPS objetivo
    irq_priority = "high",     # "high" | "normal" | "low"
    irq_stack    = 256,        # tamaño del stack de IRQ en bytes
    double_buffer = False,     # doble buffer (requiere RAM suficiente)
    update_first  = True,      # True: update→draw | False: draw→update
)
def update():
    ...

pyxel.run(update, draw)
```

### Parámetros y compatibilidad por target

| Parámetro | C64 | ZX Spectrum | CP/M | Notas |
|---|---|---|---|---|
| `sync` | `vbl`/`raster`/`cycles` | `halt`/`cycles` | `cycles` | Warning si incompatible |
| `vbl_line` | ✅ | ❌ Warning | ❌ Warning | Solo targets con raster IRQ |
| `fps` | ✅ | ✅ (ignora si `halt`) | ✅ | |
| `irq_priority` | ✅ | ✅ | ❌ Warning | CP/M no gestiona prioridad IRQ |
| `irq_stack` | ✅ | ✅ | ❌ Warning | |
| `double_buffer` | ✅ si RAM≥16KB extra | ❌ Warning | ❌ Warning | |
| `update_first` | ✅ | ✅ | ✅ | |

El transpilador emite warnings (no errores) para parámetros inaplicables en el
target seleccionado, y los ignora silenciosamente en la generación de código.

### Valores por defecto por target

```python
DEFAULTS = {
    "c64": {
        "sync": "raster", "vbl_line": 251, "fps": 50,
        "irq_priority": "high", "irq_stack": 256,
        "double_buffer": False, "update_first": True,
    },
    "zx": {
        "sync": "halt", "fps": 50,
        "irq_priority": "normal", "irq_stack": 128,
        "double_buffer": False, "update_first": True,
    },
    "cpm": {
        "sync": "cycles", "fps": 50,
        "double_buffer": False, "update_first": True,
    },
}
```

---

## Nivel 3 — Control total

```python
def my_loop():
    # El usuario gestiona todo — timing, IRQs, orden de operaciones
    while True:
        update()
        draw()

pyxel.run_custom(my_loop)
```

El transpilador genera el `main()` más minimalista posible: solo inicialización
HAL y llamada directa a la función proporcionada. Sin game loop generado, sin
IRQs configuradas, sin timing automático.

```c
/* generado para run_custom — mínimo absoluto */
#include "hal/hal.h"

void my_loop(void);

void main(void) {
    hal_init();
    my_loop();
}
```

---

## Implementación en el transpilador

### Detección en el validador (`frontend/validator.py`)

```python
# El validador busca estos patrones durante la fase de validación:

# Patrón 1: game loop automático
# pyxel.run(update, draw)

# Patrón 2: game loop parametrizado
# @pyxel.config(...) aplicado a una función + pyxel.run(fn, draw)

# Patrón 3: control total
# pyxel.run_custom(fn)
```

### Generación en el backend (`backend/codegen.py`)

El módulo de generación de código delega la emisión del `main()` al target:

```python
# En codegen.py
game_loop_mode = context.game_loop_mode   # AUTO | CONFIGURED | CUSTOM
game_loop_config = context.game_loop_config  # dict con parámetros @pyxel.config

main_c = target.generate_main(
    update_fn=context.update_fn,
    draw_fn=context.draw_fn,
    mode=game_loop_mode,
    config=game_loop_config,
)
```

Cada `targets/*.py` implementa `generate_main()` con el código C apropiado para
su hardware.
