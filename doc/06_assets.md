# Asset Baker

## Concepto

`pyxel.load()` es una **directiva de compilación**, no una llamada de función en
runtime. El transpilador la intercepta durante la validación y activa el asset
baker, que convierte el archivo `.pyxres` en arrays C estáticos embebidos en la ROM.

El binario final no contiene ninguna referencia a `pyxel.load()` ni a nombres de
archivo. Todos los assets quedan compilados como datos estáticos.

---

## Formato .pyxres

Un archivo `.pyxres` es un **ZIP estándar** con la siguiente estructura interna:

```
assets.pyxres (ZIP)
├── pyxel_version          # string con versión de Pyxel
├── image0.png             # banco de imagen 0 (128×128 px, paleta indexada 0-15)
├── image1.png             # banco de imagen 1
├── image2.png             # banco de imagen 2
├── tilemap0.json          # tilemap 0 (array de índices de tile)
├── tilemap1.json
├── tilemap2.json
├── sound0.json            # definición de sonido 0
├── ...
├── sound63.json
├── music0.json            # definición de música 0
├── ...
└── music7.json
```

---

## Pipeline del baker (`assets/baker.py`)

```
.pyxres
   │
   ├── image*.png  ──→  descomprime PNG
   │                    extrae pixels como índices 0-15
   │                    aplica palette_map del target
   │                    emite: const unsigned char IMG_BANK_N[128*128]
   │
   ├── tilemap*.json ──→ deserializa JSON (array 2D de índices)
   │                     emite: const unsigned char TILEMAP_N[W*H]
   │
   ├── sound*.json ──→  deserializa JSON
   │                    emite: structs SoundDef SOUND_N
   │
   └── music*.json ──→  deserializa JSON
                         emite: structs MusicDef MUSIC_N
```

---

## Formato de salida: `assets_gen.h`

```c
/* assets_gen.h — generado automáticamente por el asset baker */
/* NO EDITAR MANUALMENTE */

#ifndef ASSETS_GEN_H
#define ASSETS_GEN_H

#include <stddef.h>

/* ── Bancos de imagen (128×128 px, 1 byte por pixel = índice de color) ── */
extern const unsigned char IMG_BANK_0[16384];  /* 128*128 */
extern const unsigned char IMG_BANK_1[16384];
extern const unsigned char IMG_BANK_2[16384];

/* ── Tilemaps ─────────────────────────────────────────────────────────── */
/* Cada entrada es un índice de tile (0-255) */
#define TILEMAP_0_W 256
#define TILEMAP_0_H 256
extern const unsigned char TILEMAP_0[65536];   /* 256*256 */

/* ── Sonidos ──────────────────────────────────────────────────────────── */
typedef struct {
    const unsigned char *notes;    /* frecuencias MIDI-like, 0 = silencio */
    const unsigned char *tones;    /* forma de onda: 0=tri 1=sq 2=pulse 3=noise */
    const unsigned char *volumes;  /* volumen 0-7 */
    const unsigned char *effects;  /* efecto: 0=none 1=slide 2=vibrato 3=fadeout */
    unsigned char        speed;    /* velocidad en ticks */
    unsigned char        length;   /* número de notas */
} SoundDef;

extern const SoundDef SOUND_DEF_0;
/* ... hasta SOUND_DEF_63 */

/* ── Músicas ──────────────────────────────────────────────────────────── */
typedef struct {
    const unsigned char *channels[4];  /* índice de sonido por canal, 255=vacío */
    unsigned char        length;
} MusicDef;

extern const MusicDef MUSIC_DEF_0;
/* ... hasta MUSIC_DEF_7 */

#endif /* ASSETS_GEN_H */
```

---

## Conversión de paleta (`assets/palette_maps.py`)

Pyxel usa su propia paleta de 16 colores. Cada target tiene colores distintos.
El baker aplica la tabla de mapeado en el momento de leer los pixels de las imágenes.

```python
# Colores originales de Pyxel (RGB 24-bit)
PALETTE_PYXEL = [
    0x000000,  #  0 negro
    0x2b335f,  #  1 azul marino
    0x7e2072,  #  2 morado
    0x19959c,  #  3 verde azulado
    0x8b4852,  #  4 marrón rojizo
    0x395c98,  #  5 azul
    0xa9c1ff,  #  6 azul claro
    0xeeeeee,  #  7 blanco
    0xd4186c,  #  8 rojo
    0xd38441,  #  9 naranja
    0xe9c35b,  # 10 amarillo
    0x70c6a9,  # 11 verde claro
    0x7696de,  # 12 azul medio
    0xa3a3a3,  # 13 gris
    0xff9798,  # 14 rosa
    0xedc7b0,  # 15 crema
]

# Mapeado al índice de color más cercano en cada target
# El valor es el índice nativo del target para cada color Pyxel 0-15
PALETTE_MAP = {
    "c64": [
        0,   #  0 negro     → C64 negro (0)
        6,   #  1 azul mar. → C64 azul (6)
        4,   #  2 morado    → C64 violeta (4)
        3,   #  3 v.azulado → C64 cian (3)
        2,   #  4 m.rojizo  → C64 rojo (2)
        6,   #  5 azul      → C64 azul (6)
        14,  #  6 azul cla. → C64 azul claro (14)
        1,   #  7 blanco    → C64 blanco (1)
        10,  #  8 rojo      → C64 naranja claro (10)
        8,   #  9 naranja   → C64 naranja (8)
        7,   # 10 amarillo  → C64 amarillo (7)
        5,   # 11 v.claro   → C64 verde (5)
        14,  # 12 azul med. → C64 azul claro (14)
        12,  # 13 gris      → C64 gris medio (12)
        13,  # 14 rosa      → C64 gris claro (13)
        9,   # 15 crema     → C64 marrón claro (9)
    ],
    "zx": [
        0,   #  0 negro     → ZX negro (0)
        1,   #  1 azul mar. → ZX azul (1)
        2,   #  2 morado    → ZX rojo (2) — aproximación
        3,   #  3 v.azulado → ZX magenta (3) — aproximación
        4,   #  4 m.rojizo  → ZX verde (4) — aproximación
        1,   #  5 azul      → ZX azul (1)
        9,   #  6 azul cla. → ZX azul brillante (9)
        7,   #  7 blanco    → ZX blanco (7)
        10,  #  8 rojo      → ZX rojo brillante (10)
        6,   #  9 naranja   → ZX amarillo (6) — aproximación
        14,  # 10 amarillo  → ZX amarillo brillante (14)
        12,  # 11 v.claro   → ZX verde brillante (12)
        9,   # 12 azul med. → ZX azul brillante (9)
        7,   # 13 gris      → ZX blanco (7) — aproximación
        15,  # 14 rosa      → ZX blanco brillante (15)
        7,   # 15 crema     → ZX blanco (7)
    ],
}
```

---

## Acceso a assets desde el código generado

Las referencias a bancos de imagen en el script Python se traducen a accesos
directos a los arrays ROM:

```python
# Python
pyxel.blt(x, y, 0, 0, 0, 16, 16, 0)   # banco de imagen 0
```

```c
/* C generado */
hal_blt(x, y, IMG_BANK_0, 0, 0, 16, 16, 0);
```

La función `hal_blt` en cada target recibe el puntero al array ROM y copia
los pixels al framebuffer aplicando la transparencia por `colkey`.

---

## Assets completos de Pyxel: cuánto ocupan

| Asset | Especificación Pyxel | Tamaño en bruto |
|---|---|---|
| 3 bancos de imagen | 256×256 px, 4 bits/px | 98 KB |
| 8 tilemaps | 256×256 tiles, 2 bytes/tile | 1 MB |
| 64 sonidos | ~200 bytes c/u | ~12 KB |
| 8 músicas | referencias a sonidos | ~1 KB |
| **Total completo** | | **~1.1 MB** |

---

## Presupuesto de assets — por máquina, no por familia

Las restricciones de tamaño son propias de **cada máquina concreta**. No existe un
modo global ligado a la familia de CPU — cada target declara su propio presupuesto
en `targets/*.py` y el baker aplica la misma lógica para todos.

```python
# targets/c64.py
TOTAL_BUDGET_KB  = 50
CODE_RESERVE_KB  = 20
ASSET_BUDGET_KB  = 30   # calculado automáticamente si no se especifica

# targets/zx_spectrum.py
TOTAL_BUDGET_KB  = 40
CODE_RESERVE_KB  = 20
ASSET_BUDGET_KB  = 20

# targets/cpm.py
TOTAL_BUDGET_KB  = 60
CODE_RESERVE_KB  = 20
ASSET_BUDGET_KB  = 40

# targets/snes.py
TOTAL_BUDGET_KB  = 4096
CODE_RESERVE_KB  = 256
ASSET_BUDGET_KB  = 3072

# targets/amiga.py
TOTAL_BUDGET_KB  = 2048
CODE_RESERVE_KB  = 256
ASSET_BUDGET_KB  = 1792

# targets/msdos.py
TOTAL_BUDGET_KB  = 640
CODE_RESERVE_KB  = 200
ASSET_BUDGET_KB  = 400
```

El baker aplica la misma lógica para todas las máquinas:
- **Warning** si los assets superan el 60% del `ASSET_BUDGET_KB` del target
- **Error** y compilación detenida si superan el 90%
- Flags opcionales para reducir assets: `--no-tilemaps`, `--max-sounds N`, `--max-image-banks N`

```python
# assets/baker.py — lógica única para todas las máquinas
def bake(pyxres_path, target, flags):
    assets = load_pyxres(pyxres_path, flags)
    size_kb = estimate_size(assets, target)
    ratio = size_kb / target.ASSET_BUDGET_KB

    if ratio > 0.90:
        raise BakerError(
            f"Assets ({size_kb} KB) exceed budget for {target.NAME} "
            f"({target.ASSET_BUDGET_KB} KB). Use --no-tilemaps or --max-image-banks."
        )
    elif ratio > 0.60:
        warn(f"Assets use {ratio*100:.0f}% of asset budget for {target.NAME}")

    return convert_assets(assets, target)
```
