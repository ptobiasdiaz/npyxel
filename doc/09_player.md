# npyxel player — Validación y preview de assets

## Concepto

El player es el entorno de desarrollo interactivo de npyxel. Permite al desarrollador
iterar sobre un script Python sin compilar, con dos funciones principales:

1. **Validación** — ejecuta el frontend del transpilador antes de lanzar el script,
   reportando errores de subconjunto en tiempo real.

2. **Preview de assets** — cuando se especifica un target, aplica visualmente la
   conversión de paleta y restricciones del baker, mostrando exactamente cómo
   quedarán los gráficos en la máquina destino.

El player está construido sobre Pyxel — no es un emulador de hardware retro.
Su propósito es el ciclo de desarrollo, no la fidelidad de ejecución.

---

## Modos de uso

### Sin target — validación + assets originales

```bash
npyxel play script.py
```

- Ejecuta `frontend/validator.py` y `frontend/type_inference.py` sobre el script
- Si hay errores de subconjunto, los muestra y no arranca
- Si es válido, lanza el script con Pyxel mostrando los assets en su paleta original
- Útil para validar el subconjunto y desarrollar la lógica del juego

### Con target — validación + preview de assets convertidos

```bash
npyxel play script.py --target c64
npyxel play script.py --target zx
npyxel play script.py --target snes
```

- Ejecuta la validación completa (subconjunto + advertencias de presupuesto de assets)
- Convierte la paleta de los assets al mapping del target (via `assets/palette_maps.py`)
- Lanza el script con Pyxel usando los assets convertidos
- El desarrollador ve exactamente los colores que tendrá la máquina destino

---

## Flujo de ejecución

```
npyxel play script.py [--target X]
        │
        ▼
[1. VALIDACIÓN]
frontend/validator.py
        │
        ├── Errores de subconjunto → imprimir y salir
        │
        ▼
frontend/type_inference.py
        │
        ├── Errores de tipos → imprimir y salir
        │
        ▼
[2. ASSETS] (solo si hay pyxel.load() en el script)
        │
        ├── Sin --target → assets originales (pasar a Pyxel tal cual)
        │
        └── Con --target → baker.preview(pyxres, target)
                           convierte paleta en memoria
                           devuelve Image objects para Pyxel
        │
        ▼
[3. WARNINGS DE PRESUPUESTO] (solo con --target)
        │
        ├── >60% presupuesto → warning en consola
        └── >90% presupuesto → warning prominente (no bloquea ejecución)
        │
        ▼
[4. LANZAMIENTO]
Pyxel ejecuta el script con los assets (originales o convertidos)
```

---

## Modo preview del baker

El baker tiene dos modos de salida que comparten la misma lógica de conversión:

```python
# assets/baker.py

def compile(pyxres_path, target, flags):
    """Modo compilación: emite assets_gen.c y assets_gen.h"""
    assets = load_pyxres(pyxres_path, flags)
    _check_budget(assets, target)
    converted = _convert(assets, target)
    return emit_c(converted)

def preview(pyxres_path, target):
    """Modo preview: devuelve assets convertidos en memoria para Pyxel"""
    assets = load_pyxres(pyxres_path)
    _check_budget(assets, target, warn_only=True)
    converted = _convert(assets, target)
    return to_pyxel_images(converted)   # devuelve lista de pyxel.Image
```

`_convert()` es exactamente la misma función en ambos modos — aplica
`palette_maps.py` y escala/recorta si el target tiene restricciones de tamaño.
La única diferencia es el formato de salida.

---

## Conversión de paleta en el player

Cuando se especifica `--target`, el player intercepta `pyxel.load()` y sustituye
los bancos de imagen con versiones con la paleta convertida:

```python
# preview/runner.py

import pyxel
from assets.baker import preview as baker_preview
from assets.palette_maps import PALETTE_MAP

def patch_load(target):
    """Monkey-patch de pyxel.load() para interceptar y convertir assets."""
    original_load = pyxel.load

    def patched_load(filename, **kwargs):
        original_load(filename, **kwargs)
        converted = baker_preview(filename, target)
        for i, img in enumerate(converted.images):
            pyxel.images[i].set(0, 0, img.data)

    pyxel.load = patched_load
```

Esto es transparente para el script del usuario — sigue llamando a `pyxel.load()`
con normalidad y ve los assets convertidos sin saber que hubo una intercepción.

---

## Visualización de advertencias

Las advertencias de presupuesto se muestran en consola antes del arranque, no
como overlay en pantalla (para no interferir con el rendering del script):

```
npyxel play mygame.py --target c64

✓ Subset validation passed
✓ Type inference passed
⚠ Assets use 74% of asset budget for C64 (22.2 KB / 30 KB)
  Consider using --no-tilemaps or --max-image-banks 1
▶ Launching with C64 palette preview...
```

Si hay errores de subconjunto, el player no arranca:

```
npyxel play mygame.py --target c64

✗ Subset validation failed:
  line 42: 'try/except' is not supported
  line 17: class inheritance is not allowed — 'class B(A)' found
```

---

## Estructura de archivos

```
npyxel/
└── preview/
    ├── __main__.py        # entry point: npyxel play script.py [--target X]
    ├── runner.py          # orquesta validación, baker preview y lanzamiento Pyxel
    ├── patcher.py         # monkey-patch de pyxel.load() para assets convertidos
    └── reporter.py        # formato de mensajes de error y warning en consola
```

---

## Ciclo de desarrollo recomendado

```
1. npyxel play script.py
   → desarrollo rápido, assets originales, validación de subconjunto

2. npyxel play script.py --target c64
   → verificar aspecto visual con paleta C64, ver warnings de presupuesto

3. python -m npyxel script.py --target c64 --output game.prg
   → compilación final cuando el preview es satisfactorio

4. Probar game.prg en VICE (emulador C64) o hardware real
```

Los pasos 1 y 2 son iterativos y rápidos. El paso 3 solo se hace cuando
el script está listo — es el equivalente al "build" final.

---

## Limitaciones conocidas

El player **no** emula el hardware retro. Las siguientes diferencias son
inherentes al enfoque y no se consideran bugs:

| Aspecto | En el player | En el target real |
|---|---|---|
| Velocidad | Velocidad del host moderno | Velocidad de la CPU retro |
| Sonido | Síntesis Pyxel (no SID/beeper) | Hardware nativo |
| Resolución | Escala Pyxel en ventana | Resolución fija del target |
| Color | Paleta convertida (aproximación) | Colores exactos del hardware |
| Sprites | Software (Pyxel) | Hardware (VIC-II, PPU, Blitter) |

Para fidelidad total se usa el emulador del target (VICE, ZEsarUX, fs-uae, DOSBox)
con el binario compilado.
