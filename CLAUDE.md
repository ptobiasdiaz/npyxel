# npyxel — Native Pyxel — Transpilador Python/Pyxel para arquitecturas retro

## Qué es este proyecto

Transpilador de source-to-source que convierte scripts Python (subconjunto acotado, API Pyxel)
en binarios nativos para arquitecturas retro de 8 y 16 bits.

El usuario escribe en Python usando la API de Pyxel. El transpilador genera C89, lo compila con
el toolchain del target y empaqueta el binario final.

**No hay intérprete en el target.** El hardware retro ejecuta únicamente código nativo.

## Dos familias

El número del paquete identifica la **generación de arquitectura de CPU**, no una
capacidad o restricción. Ambas familias crecen en número de máquinas soportadas
con cada release. Las restricciones de assets y memoria son propias de cada
**máquina concreta**, no de la familia.

### npyxel8 — familias Z80 y 6502
Soporta máquinas basadas en **Zilog Z80** y **MOS 6502** (y derivados: Z180, 65C02, 6510...).
El catálogo de máquinas crece con cada release — siempre dentro de estas dos familias de CPU.

Máquinas iniciales: Commodore 64 (6510), ZX Spectrum (Z80), CP/M genérico (Z80).
Toolchain: cc65 (familia 6502), z88dk/SDCC (familia Z80).
Salida típica: `.prg`, `.tap`, `.com`

### npyxel16 — familias 65816, 68000 y x86
Soporta máquinas basadas en **Ricoh 5A22 / WDC 65816**, **Motorola 68000**
e **Intel 8086/88** (y derivados). El catálogo de máquinas crece con cada release.

Máquinas iniciales: SNES/Super Famicom (5A22), Amiga 500 (68000), MS-DOS (i8086).
Toolchain: PVSnesLib/ca65 (65816), GCC m68k-amigaos / VBCC (68000), OpenWatcom (x86).
Salida típica: `.sfc`, `.adf`/`.lha`, `.exe`

### Compatibilidad entre familias
El subconjunto Python es **100% compatible**. Un script válido en npyxel8 compila
en npyxel16 sin modificaciones. Las diferencias (assets, resolución, sonido) son
propias del hardware destino, no del lenguaje ni la API.

### Añadir soporte a una nueva máquina
El transpilador, baker y frontend son agnósticos al target. Para incorporar una
nueva máquina se necesita únicamente:
1. Una clase en `targets/` que implemente `BaseTarget`
2. Una implementación de la HAL en `hal/<nombre_maquina>/`
3. Las tablas de paleta en `assets/palette_maps.py`

## Documentación de referencia

Leer en este orden antes de implementar cualquier módulo:

- `docs/01_subset.md` — Subconjunto Python soportado (qué está permitido y qué no)
- `docs/02_pipeline.md` — Arquitectura completa del transpilador (5 etapas)
- `docs/03_pyxel_api.md` — API Pyxel soportada, adaptada y excluida
- `docs/04_hal.md` — Hardware Abstraction Layer: estructura y contratos por target
- `docs/05_gameloop.md` — Generación del game loop: automático, parametrizado y manual
- `docs/06_assets.md` — Asset baker: presupuestos por máquina, conversión de formatos
- `docs/07_targets_8bit.md` — Targets npyxel8 (familias Z80/6502): C64, ZX Spectrum, CP/M
- `docs/08_targets_16bit.md` — Targets npyxel16 (familias 65816/68000/x86): SNES, Amiga, MS-DOS
- `docs/09_player.md`       — Player: validación de subconjunto y preview de assets por target

## Estructura del proyecto

```
npyxel/
├── CLAUDE.md                  # Este archivo
├── docs/                      # Especificaciones detalladas
├── transpiler/
│   ├── frontend/
│   │   ├── validator.py       # Valida el subconjunto — EMPEZAR AQUÍ
│   │   └── type_inference.py  # Inferencia de tipos + tabla de símbolos
│   ├── backend/
│   │   ├── codegen.py         # AST → C89
│   │   └── hal_signatures.py  # Firmas de funciones HAL conocidas
│   ├── assets/
│   │   ├── baker.py           # .pyxres → arrays C (compile) o pyxel.Image (preview)
│   │   └── palette_maps.py    # Tablas de paleta por target
│   ├── targets/
│   │   ├── base.py            # Clase abstracta Target
│   │   ├── c64.py             # npyxel8
│   │   ├── cpm.py             # npyxel8
│   │   ├── zx_spectrum.py     # npyxel8
│   │   ├── snes.py            # npyxel16
│   │   ├── amiga.py           # npyxel16
│   │   └── msdos.py           # npyxel16
│   └── preview/
│       ├── __main__.py        # entry point: npyxel play script.py [--target X]
│       ├── runner.py          # orquesta validación, baker preview y lanzamiento
│       ├── patcher.py         # monkey-patch de pyxel.load() para assets convertidos
│       └── reporter.py        # formato de errores y warnings en consola
└── hal/
    ├── common/                # Algoritmos portables (Bresenham, etc.)
    ├── c64/                   # VIC-II, SID, CIA
    ├── cpm/                   # Consola, beeper, teclado
    ├── zx/                    # ULA, beeper, teclado
    ├── snes/                  # PPU, APU, joypad
    ├── amiga/                 # Blitter, Paula, CIA
    └── msdos/                 # VGA/EGA, OPL2/SB, teclado
```

## Decisiones de diseño clave

1. `pyxel.load()` y `@pyxel.config` son **directivas de compilación**, no llamadas de función.
   Desaparecen del binario final.

2. El módulo `ast` de Python hace el parsing. No hay parser propio.

3. La inferencia de tipos es local y estática. Si falla, se exige anotación explícita (PEP 526).

4. Las variables C89 se declaran al inicio del bloque (pre-scan de scope obligatorio).

5. El game loop tiene tres niveles: automático / parametrizado (`@pyxel.config`) / total (`run_custom`).

6. Los assets se convierten al formato nativo del target en tiempo de compilación (paleta incluida).

7. Las restricciones de assets y memoria son propias de **cada máquina concreta**, no de
   la familia. El baker calcula el presupuesto según los parámetros declarados en `targets/*.py`.

8. Un script válido en npyxel8 compila en npyxel16 sin modificaciones (compatibilidad ascendente).

9. El catálogo de máquinas soportadas crece con cada release. El core del transpilador
   no requiere modificaciones al añadir nuevas máquinas — solo un nuevo `targets/*.py` y `hal/*/`.

## Comandos de uso previstos

```bash
# Player — desarrollo iterativo
npyxel play script.py                   # validación + assets originales Pyxel
npyxel play script.py --target c64      # validación + preview con paleta C64
npyxel play script.py --target snes     # validación + preview con paleta SNES

# Compilación final
# npyxel8 — familia Z80 y 6502
python -m transpiler script.py --target c64      --output game.prg
python -m transpiler script.py --target zx       --output game.tap
python -m transpiler script.py --target cpm      --output game.com

# npyxel16 — familias 65816, 68000 y x86
python -m transpiler script.py --target snes     --output game.sfc
python -m transpiler script.py --target amiga    --output game.adf
python -m transpiler script.py --target msdos    --output game.exe
```

## Stack tecnológico

- **Transpilador**: Python 3.10+, módulo `ast` estándar
- **npyxel8 / 6502**: cc65 / cl65
- **npyxel8 / Z80**: z88dk (zcc + zsdcc)
- **npyxel16 / SNES**: PVSnesLib + ca65
- **npyxel16 / 68000**: GCC m68k-amigaos o VBCC
- **npyxel16 / MS-DOS**: OpenWatcom (modo real 16 bits)
- **Assets**: formato .pyxres (ZIP interno), Pillow para conversión de imágenes
