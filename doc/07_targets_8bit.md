# Targets npyxel8 — arquitecturas de 8 bits

## Targets soportados

| Target | CPU | Toolchain | Salida |
|---|---|---|---|
| Commodore 64 | MOS 6510 (6502) | cc65 / cl65 | `.prg` |
| ZX Spectrum | Zilog Z80 | z88dk (zcc + zsdcc) | `.tap` / `.tzx` |
| CP/M | Zilog Z80 | z88dk (zcc + zsdcc) | `.com` |

Otros sistemas basados en 6502 (Apple II, NES, Atari 8-bit) o Z80 (MSX, Amstrad CPC)
pueden añadirse implementando una nueva clase en `targets/` y su correspondiente HAL.

---

## Commodore 64

### Hardware relevante

| Chip | Función | Registros clave |
|---|---|---|
| VIC-II ($D000) | Gráficos | $D000–$D3FF |
| SID ($D400) | Sonido | $D400–$D41C |
| CIA1 ($DC00) | Teclado / joystick | $DC00, $DC01 |
| CIA2 ($DD00) | NMI / banco de memoria | $DD00 |

### Modos gráficos

El C64 ofrece varios modos. Para npyxel8 se usa **bitmap hires** (320×200, 2 colores
por celda 8×8) o **bitmap multicolor** (160×200, 4 colores por celda 4×8).

El baker selecciona el modo según la paleta usada en los assets:
- Si cada celda 8×8 usa ≤2 colores → hires (más resolución)
- Si usa hasta 4 → multicolor (más color, mitad de resolución horizontal)

**Organización de memoria sugerida:**

```
$0000–$00FF  Zero page (variables frecuentes)
$0100–$01FF  Stack hardware 6502
$0200–$07FF  Variables C, buffers
$0800–$0FFF  Código del programa (generado)
$1000–$1FFF  HAL + rutinas ASM
$2000–$3FFF  Bitmap screen ($2000, 8KB)
$4000–$7FFF  Assets (imagen, tilemaps, sonidos) — hasta 16 KB
$8000–$BFFF  Código adicional si necesario
$C000–$CFFF  Color RAM mirror / uso libre
$D000–$DFFF  Registros I/O (VIC-II, SID, CIA)
$E000–$FFFF  KERNAL ROM (banqueable)
```

### Toolchain

```bash
cl65 -t c64 -O -C c64-asm.cfg \
     -o game.prg \
     main.c assets_gen.c \
     ../../hal/c64/graphics.c \
     ../../hal/c64/sound.c \
     ../../hal/c64/input.c \
     ../../hal/common/bresenham.c
```

### HAL: hal/c64/

**graphics.c** — VIC-II
- `hal_init()`: configura modo bitmap, banco de memoria VIC-II, color RAM
- `hal_cls()`: limpia bitmap ($2000) y color RAM ($D800) — inline ASM recomendado
- `hal_pset()`: calcula dirección en bitmap y actualiza color RAM
- `hal_blt()`: copia desde array ROM con comprobación de colkey

**sound.c** — SID
- `hal_play()`: programa voz SID según `SoundDef` del asset baker
- Envelope ADSR, forma de onda y frecuencia vía registros $D400–$D41C
- Implementación en ASM puro para timing correcto

**input.c** — CIA1
- `hal_btn()`: lee joystick puerto 2 ($DC00, bits 0–4) o teclado (matriz $DC00/$DC01)
- `hal_btnp()`: edge detection con contador de frames para auto-repeat

**gameloop.c**
- Raster IRQ del VIC-II en línea 251 (debajo del área visible)
- Ver docs/05_gameloop.md para el código generado

### Paleta

El C64 tiene exactamente 16 colores — coincide con Pyxel. El mapeado no es perfecto
cromáticamente pero es 1:1 en número de colores. Ver `assets/palette_maps.py`.

---

## ZX Spectrum

### Hardware relevante

| Componente | Función |
|---|---|
| ULA | Gráficos + sonido beeper |
| Pixel buffer | $4000–$57FF (6144 bytes) |
| Atributos | $5800–$5AFF (768 bytes, celdas 8×8) |
| Puerto $FE | Beeper (bit 4) + borde |
| Puerto $FE read | Teclado (semifilas) |

### Limitación crítica de color

El Spectrum tiene la restricción de **2 colores por celda de 8×8 píxeles**
(1 de tinta + 1 de papel). Es la limitación más severa de los targets npyxel8.

El baker lo gestiona así:
- Por cada celda 8×8 de los assets, detecta los 2 colores más usados
- Asigna tinta/papel en el atributo correspondiente
- Los píxeles con colores minoritarios se aproximan al más cercano disponible
- Emite warning con el número de celdas que tuvieron conflicto de color

### Organización de memoria

```
$4000–$57FF  Pixel buffer (organización no lineal por tercios)
$5800–$5AFF  Atributos de color
$5B00–$5FFF  Sistema
$6000–$FFFF  Programa (código + assets + stack)
```

**Nota:** la organización no lineal del pixel buffer es la parte más compleja de
la HAL del Spectrum. La dirección de un pixel (x, y) se calcula:

```
línea dentro del tercio = y & 0x07
tercio                  = (y >> 3) & 0x18
fila dentro del tercio  = (y >> 3) & 0x07
dirección = 0x4000 | (tercio << 8) | (fila << 5) | (x >> 3)
```

Esto requiere inline ASM o lógica de bits cuidadosa en C89.

### Toolchain

```bash
zcc +zx -O2 -o game_zx.bin \
    main.c assets_gen.c \
    ../../hal/zx/graphics.c \
    ../../hal/zx/sound.c \
    ../../hal/zx/input.c \
    ../../hal/common/bresenham.c

# Empaquetado en cinta
appmake +zx --binfile game_zx.bin --org 32768 -o game.tap
```

### HAL: hal/zx/

**graphics.c** — ULA
- `hal_pset()`: calcula dirección no lineal, actualiza pixel y atributo
- `hal_cls()`: limpia pixel buffer y atributos con valores de color por defecto

**sound.c** — beeper
- Generación de tonos por bit-banging del bit 4 del puerto $FE
- Timing ciclo-exacto → ASM puro obligatorio
- Solo un tono a la vez (beeper monofónico)
- `hal_play()` en ZX solo usa el canal 0; los canales 1–3 se ignoran con warning

**input.c** — matriz de teclado
- Lectura por semifilas via puerto $FE
- Mapeo de teclas/joystick Kempston ($1F)

---

## CP/M

### Características

CP/M es un sistema operativo, no hardware específico. Los targets CP/M son
máquinas Z80 genéricas con terminal de texto.

- Sin hardware gráfico estándar
- Acceso a hardware via BDOS (Basic Disk Operating System) y BIOS calls
- Terminal de texto ANSI/VT100 como salida gráfica (escape codes)

### Variantes soportadas

| Variante | Display | Notas |
|---|---|---|
| CP/M genérico | ANSI escape codes | Terminal compatible VT100 |
| RC2014 + VDP | TMS9918A | Chip gráfico opcional popular |
| CP/M + CGA | Puerto serie a PC | Configuración menos común |

Se selecciona con `--display ansi` (defecto) o `--display tms9918`.

### Toolchain

```bash
zcc +cpm -O2 -o game.com \
    main.c assets_gen.c \
    ../../hal/cpm/graphics.c \
    ../../hal/cpm/sound.c \
    ../../hal/cpm/input.c \
    ../../hal/common/bresenham.c
```

### HAL: hal/cpm/

**graphics.c** — ANSI/VT100
- `hal_cls()`: `\033[2J\033[H`
- `hal_pset()`: `\033[y;xH\033[48;5;Nm ` (carácter de bloque con color de fondo)
- Resolución efectiva limitada por el tamaño del terminal (típicamente 80×24)
- El baker escala los assets al tamaño del terminal si es necesario

**sound.c** — beeper via BDOS
- `\007` (BEL) para sonido básico
- Sin control de frecuencia en CP/M genérico

**gameloop.c** — timing por ciclos
- Sin VBL — `hal_wait_cycles()` implementado via bucle calibrado o timer del sistema
