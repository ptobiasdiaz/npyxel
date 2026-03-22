# npyxel — Native Pyxel

Transpilador source-to-source que convierte scripts Python escritos con la API de Pyxel
en binarios nativos para hardware retro de 8 y 16 bits.

**No hay intérprete en el target.** El usuario escribe en Python; el hardware retro ejecuta código nativo.

## Cómo funciona

```
script.py (Python + API Pyxel)
        │
        ▼
   [Validator]  ──── detecta construcciones no soportadas
        │
   [Type inference]  ──── tabla de símbolos, anotaciones PEP 526
        │
   [Codegen]  ──── genera C89
        │
   [Toolchain]  ──── cc65 / z88dk / PVSnesLib / GCC m68k / OpenWatcom
        │
        ▼
   binario nativo (.prg / .tap / .sfc / .adf / .exe …)
```

El módulo `ast` de Python hace el parsing. No hay parser propio.
`pyxel.load()` y `@pyxel.config` son directivas de compilación: desaparecen del binario final.

## Familias de targets

### npyxel8 — Z80 y 6502
Máquinas basadas en **Zilog Z80** y **MOS 6502** (y derivados: Z180, 65C02, 6510…).

| Máquina        | CPU   | Toolchain  | Salida    |
|----------------|-------|------------|-----------|
| Commodore 64   | 6510  | cc65/cl65  | `.prg`    |
| ZX Spectrum    | Z80   | z88dk/SDCC | `.tap`    |
| CP/M genérico  | Z80   | z88dk/SDCC | `.com`    |

### npyxel16 — 65816, 68000 y x86
Máquinas basadas en **Ricoh 5A22 / WDC 65816**, **Motorola 68000** e **Intel 8086/88**.

| Máquina              | CPU    | Toolchain           | Salida      |
|----------------------|--------|---------------------|-------------|
| SNES / Super Famicom | 5A22   | PVSnesLib + ca65    | `.sfc`      |
| Amiga 500            | 68000  | GCC m68k-amigaos    | `.adf`/`.lha` |
| MS-DOS               | i8086  | OpenWatcom          | `.exe`      |

Un script válido en npyxel8 compila en npyxel16 sin modificaciones.

## Instalación

Requiere **Python 3.10+** y **Pyxel** para el player.

```bash
pip install pyxel
git clone https://github.com/your-org/npyxel
cd npyxel
```

> Los toolchains de compilación (cc65, z88dk, OpenWatcom…) solo son necesarios
> para generar el binario final, no para el player.

## Player — desarrollo iterativo

El player valida el subconjunto y lanza el script directamente sobre Pyxel,
sin compilar. Útil para iterar rápido sin necesitar el toolchain del target.

```bash
python -m transpiler.preview play examples/hello.py
```

Salida esperada:

```
✓ Subset validation passed
✓ Type inference passed
▶ Launching...
```

Si el script contiene construcciones no soportadas, el player las reporta con
número de línea y aborta antes de lanzar:

```
✗ Subset validation failed:
  ERROR line   7: 'try/except' is not supported in this subset
  ERROR line  12: class inheritance is not allowed
```

## Compilación final

```bash
# npyxel8 — familia Z80 y 6502
python -m transpiler script.py --target c64      --output game.prg
python -m transpiler script.py --target zx       --output game.tap
python -m transpiler script.py --target cpm      --output game.com

# npyxel16 — familias 65816, 68000 y x86
python -m transpiler script.py --target snes     --output game.sfc
python -m transpiler script.py --target amiga    --output game.adf
python -m transpiler script.py --target msdos    --output game.exe
```

## Estructura del proyecto

```
npyxel/
├── transpiler/
│   ├── frontend/
│   │   ├── validator.py       # Valida el subconjunto — punto de entrada
│   │   └── type_inference.py  # Inferencia de tipos + tabla de símbolos
│   ├── backend/
│   │   ├── codegen.py         # AST → C89
│   │   └── hal_signatures.py  # Firmas de funciones HAL
│   ├── assets/
│   │   ├── baker.py           # .pyxres → arrays C / pyxel.Image
│   │   └── palette_maps.py    # Tablas de paleta por target
│   ├── targets/               # Un archivo por máquina (implementan BaseTarget)
│   └── preview/               # Player: validación + lanzamiento con Pyxel
├── hal/                       # HAL en C por máquina
├── examples/
│   ├── hello.py
│   └── pong.py
└── docs/                      # Especificaciones detalladas (01_subset … 09_player)
```

## Añadir soporte a una nueva máquina

El core del transpilador no requiere modificaciones. Solo se necesita:

1. Una clase en `transpiler/targets/` que implemente `BaseTarget`
2. Una implementación de la HAL en `hal/<nombre_maquina>/`
3. Las tablas de paleta en `transpiler/assets/palette_maps.py`

## Documentación

La carpeta `docs/` contiene las especificaciones completas, en este orden de lectura:

| Documento          | Contenido                                              |
|--------------------|--------------------------------------------------------|
| `01_subset.md`     | Subconjunto Python soportado                           |
| `02_pipeline.md`   | Arquitectura del transpilador (5 etapas)               |
| `03_pyxel_api.md`  | API Pyxel soportada, adaptada y excluida               |
| `04_hal.md`        | Hardware Abstraction Layer: estructura y contratos     |
| `05_gameloop.md`   | Generación del game loop                               |
| `06_assets.md`     | Asset baker: presupuestos y conversión de formatos     |
| `07_targets_8bit.md`  | Targets npyxel8: C64, ZX Spectrum, CP/M            |
| `08_targets_16bit.md` | Targets npyxel16: SNES, Amiga, MS-DOS              |
| `09_player.md`     | Player: validación y preview de assets                 |
