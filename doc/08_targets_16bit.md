# Targets npyxel16 — arquitecturas de 16 bits

## Targets soportados

| Target | CPU | Toolchain | Salida |
|---|---|---|---|
| SNES / Super Famicom | Ricoh 5A22 (65816) | PVSnesLib + ca65 | `.sfc` |
| Amiga / sistemas 68000 | Motorola 68000 | GCC m68k-amigaos / VBCC | `.adf` / `.lha` |
| MS-DOS | Intel i8086 (modo real) | OpenWatcom | `.exe` |

Los tres targets tienen espacio suficiente para los assets completos de Pyxel
(~1.1 MB) sin restricciones prácticas.

---

## SNES / Super Famicom

### Hardware relevante

| Chip | Función | Notas |
|---|---|---|
| Ricoh 5A22 | CPU (65816 a 3.58 MHz) | 16 bits, compatible 6502 en modo emulación |
| PPU (Picture Processing Unit) | Gráficos | 2 chips: PPU1 + PPU2 |
| SPC700 | CPU de sonido | Procesador independiente con 64 KB de RAM |
| DSP | Síntesis de sonido | 8 canales, muestras ADPCM (formato BRR) |
| DMA / HDMA | Transferencia de datos | Crítico para rendimiento gráfico |

### Capacidades gráficas

El SNES tiene un sistema de capas (backgrounds) y sprites hardware muy potente:

| Modo PPU | Capas | Colores | Uso recomendado |
|---|---|---|---|
| Mode 0 | 4 BG (2bpp cada una) | 32 colores | Múltiples capas simples |
| Mode 1 | 2 BG 4bpp + 1 BG 2bpp | 128+32 col. | **Más usado en juegos** |
| Mode 7 | 1 BG con rotación/escala | 256 colores | Efectos 3D pseudo |

Para npyxel16/SNES se usa **Mode 1** por defecto, que ofrece el mejor balance.

**Sprites hardware:** hasta 128 sprites de 8×8 u 16×16 píxeles, 16 colores cada uno.
El blitter de Pyxel (`hal_blt`) puede aprovechar los sprites hardware para elementos
pequeños y el DMA para copias de fondo.

### Assets en SNES

El formato nativo del SNES para gráficos es **tile-based de 4bpp** (16 colores),
lo que encaja perfectamente con la paleta de 16 colores de Pyxel.

El baker convierte los bancos de imagen al formato SNES 4bpp tile (8×8 píxeles por tile)
y los carga en VRAM via DMA. Los tilemaps de Pyxel (256×256 tiles) se convierten al
formato de tilemap de la PPU.

El sonido requiere conversión de las notas Pyxel a muestras BRR (Bit Rate Reduction)
para el DSP del SPC700. El baker genera las muestras BRR desde formas de onda sintéticas
(triangle, square, pulse, noise) que emulan los 4 tipos de tono de Pyxel.

### Organización de memoria SNES

```
Bank $00–$3F  ROM (programa + datos) — hasta 4 MB en LoROM
Bank $7E      WRAM página 0 (64 KB — variables, stack)
Bank $7F      WRAM página 1 (64 KB — buffers)
VRAM          64 KB — tilemaps y tiles de la PPU
CGRAM         512 bytes — paleta (256 colores × 2 bytes)
OAM           544 bytes — tabla de sprites
SPC RAM       64 KB — programa y muestras de sonido del SPC700
```

### Toolchain

```bash
# PVSnesLib es el SDK C más completo para SNES
# Incluye ca65 como ensamblador y un linker propio

make -f pvsnesmake SRCS="main.c assets_gen.c hal/snes/graphics.c \
     hal/snes/sound.c hal/snes/input.c hal/common/bresenham.c"
# Genera game.sfc directamente
```

### HAL: hal/snes/

**graphics.c** — PPU
- `hal_init()`: configura Mode 1, inicializa DMA, carga paleta en CGRAM
- `hal_cls()`: limpia tilemap activo via DMA
- `hal_pset()`: escribe tile y paleta en VRAM (operación costosa — usar con moderación)
- `hal_blt()`: copia tiles desde VRAM usando hardware sprites o DMA según tamaño
- `hal_bltm()`: escribe tilemap completo via HDMA para máximo rendimiento

**sound.c** — SPC700/DSP
- `hal_play()`: envía comando al SPC700 via puertos $2140–$2143
- 4 canales de Pyxel → 4 de los 8 canales DSP del SNES
- Muestras BRR precalculadas por el baker para cada forma de onda

**input.c** — joypad
- Lectura via registros $4016/$4017 (lectura serie del joypad)
- Soporte para los dos puertos de joypad del SNES
- Mapeo de botones SNES (A, B, X, Y, L, R, Start, Select) a constantes Pyxel

**gameloop.c**
- NMI (Non-Maskable Interrupt) al inicio del VBlank — 60Hz (NTSC) o 50Hz (PAL)
- Es el equivalente SNES de la raster IRQ del C64

---

## Amiga / sistemas Motorola 68000

### Hardware relevante (Amiga 500/1000/2000)

| Chip | Función | Notas |
|---|---|---|
| Motorola 68000 | CPU a 7.16 MHz | 32 bits internos, bus de 16 bits |
| Agnus | DMA master, Blitter, Copper | El chip más importante para gráficos |
| Denise | Display, sprites | Genera la señal de vídeo |
| Paula | Sonido (4 canales DMA), I/O | Audio PCM de 8 bits |
| CIA A/B | Timers, teclado, joystick | Equivalente a la CIA del C64 |

### Capacidades gráficas

El Amiga tiene varios modos Playfield. Para npyxel16 se usa **OCS/ECS lowres**:
- 320×256 (PAL) o 320×200 (NTSC)
- Hasta 32 colores en modo normal (5 bitplanes)
- Hasta 64 colores en Extra Half-Brite (EHB)
- Hasta 4096 colores en Hold-And-Modify (HAM) — no usado en npyxel16

El **Blitter** hardware del Amiga es especialmente poderoso para copiar sprites
y fondos — `hal_blt` lo aprovecha directamente, siendo mucho más rápido que
en cualquier target de 8 bits.

El **Copper** (coprocesador de la PPU) permite cambiar colores y modos en mitad
del raster, técnica usada para efectos visuales avanzados.

### Assets en Amiga

El Amiga usa bitplanes: cada plano de bits es una capa de 1 bit por píxel.
5 bitplanes = 32 colores. El baker convierte los bancos de imagen Pyxel (16 colores,
4bpp indexado) a formato bitplane interleaved o non-interleaved.

El sonido usa **muestras PCM de 8 bits** reproducidas por DMA via Paula.
El baker genera muestras sintéticas para cada forma de onda Pyxel (triangle, square,
pulse, noise) a 8-bit signed PCM.

### Toolchain

```bash
# GCC m68k-amigaos (toolchain moderno para Amiga)
m68k-amigaos-gcc -O2 -o game \
    main.c assets_gen.c \
    hal/amiga/graphics.c \
    hal/amiga/sound.c \
    hal/amiga/input.c \
    hal/common/bresenham.c \
    -lamiga

# Empaquetado
makedir game_disk/s
copy game game_disk/game
echo "game" > game_disk/s/startup-sequence
amitools xdftool game.adf create + format "GameDisk" OFS
amitools xdftool game.adf write game_disk
```

Alternativa: **VBCC** (compilador nativo más ligero, sin dependencias GNU).

### HAL: hal/amiga/

**graphics.c** — Blitter + Copper
- `hal_init()`: configura bitplanes, Copper list, paleta de 16 colores en CLUT
- `hal_cls()`: limpia todos los bitplanes via Blitter (velocidad máxima)
- `hal_pset()`: escribe pixel en los 4 bitplanes correspondientes
- `hal_blt()`: usa Blitter hardware para copias de área — muy eficiente
- `hal_bltm()`: Blitter + Copper para tilemaps scrollables

**sound.c** — Paula
- 4 canales de audio DMA directamente mapeados a los 4 canales de Pyxel
- `hal_play()`: configura puntero DMA, longitud y período de muestra en Paula
- Período = clock Paula / frecuencia deseada

**input.c** — CIA + joystick
- Joystick: puertos $BFE001 (port 1) y $BFD100 (port 2) via CIA A
- Teclado: interrupciones CIA A, mapeo de keycodes Amiga a constantes Pyxel

---

## MS-DOS — Intel i8086 (modo real 16 bits)

### Entorno

- CPU: i8086/i8088/i286 en modo real (1 MB de espacio de direcciones)
- Memoria convencional: 640 KB (segmentos de 64 KB, direccionamiento segmentado)
- Modo gráfico: **VGA Mode 13h** (320×200, 256 colores) o **EGA Mode 0Dh** (320×200, 16 colores)
- Sonido: PC speaker, OPL2 (AdLib), Sound Blaster (PCM)

El modo real implica limitaciones de segmentación que el compilador (OpenWatcom
en modelo de memoria `small` o `medium`) gestiona automáticamente.

### Modo gráfico recomendado: VGA Mode 13h

Mode 13h es el modo gráfico más simple y rápido de DOS:
- 320×200 píxeles, 256 colores (paleta DAC de 18 bits)
- Framebuffer lineal en $A0000 (64 KB)
- 1 byte por píxel = acceso directo sin bitplanes

Los 16 colores de Pyxel se mapean a 16 entradas de la paleta VGA de 256.
El resto de la paleta puede quedar a cero o usarse para efectos de fade/palette cycling.

### Assets en MS-DOS

Con el disco como almacenamiento, los assets completos de Pyxel no tienen
restricción práctica de tamaño. El baker genera `assets_gen.c` con todos los
bancos de imagen en formato Mode 13h (1 byte por pixel, índice de paleta).

### Organización de memoria (modelo Small)

```
Segmento 0000  IVT (Interrupt Vector Table)
Segmento 0040  BIOS Data Area
...
Segmento de código (CS)  hasta 64 KB — código del programa
Segmento de datos  (DS)  hasta 64 KB — variables, assets pequeños
Stack (SS)               hasta 64 KB
$A000:0000               Framebuffer VGA (64 KB)
```

Para assets grandes (>64 KB) se necesita el modelo de memoria `large` o `huge`,
que OpenWatcom soporta pero implica far pointers. El transpilador selecciona
automáticamente `large` si los assets superan 60 KB.

### Toolchain

```bash
# OpenWatcom — compilador C para DOS en modo real
wcl -bt=dos -ms -O2 -fo=.obj \
    main.c assets_gen.c \
    hal/msdos/graphics.c \
    hal/msdos/sound.c \
    hal/msdos/input.c \
    hal/common/bresenham.c
# -ms = modelo small, -bt=dos = target DOS

# Resultado: game.exe ejecutable DOS
```

### HAL: hal/msdos/

**graphics.c** — VGA Mode 13h
- `hal_init()`: establece modo 13h via INT 10h (AX=0013h), configura paleta DAC
- `hal_cls()`: `memset((void far*)0xA0000000, color, 64000)` — limpia framebuffer
- `hal_pset()`: `((unsigned char far*)0xA0000000)[y*320+x] = col`
- `hal_blt()`: `memcpy` desde array ROM al framebuffer con comprobación de colkey
- `hal_flip()`: sin doble buffer en mode 13h por defecto (opcional via buffer en RAM)

**sound.c** — PC speaker / AdLib
- PC speaker: timing via PIT (Programmable Interval Timer, puerto $42/$43)
- AdLib (OPL2): programación de registros via puertos $388/$389
- Sound Blaster PCM: via DSP del SB (detección por variable de entorno `BLASTER`)
- El target selecciona la implementación de sonido via flag `--sound speaker|adlib|sb`

**input.c** — teclado DOS
- `hal_btn()`: via INT 16h (BIOS keyboard) o lectura directa del buffer $0041:001E
- `hal_btnp()`: polling del estado de teclas con edge detection

**gameloop.c**
- Sin VBL hardware accesible en modo real estándar
- Timing via INT 08h (timer del sistema, 18.2 Hz por defecto) o reprogramación del PIT
- Con PIT reprogramado: hasta 1000 Hz de resolución temporal
- Por defecto se usa `@pyxel.config(sync="cycles", fps=60)`
