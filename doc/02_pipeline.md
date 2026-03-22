# Arquitectura del transpilador

## Pipeline completa

```
script.py + assets.pyxres
         │
    ┌────▼─────┐
    │ FRONTEND │  módulo ast de Python → AST validado
    └────┬─────┘  validator.py rechaza construcciones fuera del subconjunto
         │
    ┌────▼──────┐
    │ ANÁLISIS  │  type_inference.py → AST anotado con tipos
    └────┬──────┘  tabla de símbolos + registro de clases
         │
    ┌────▼────────┐
    │   BACKEND   │  codegen.py → archivos .c y .h
    └────┬────────┘  hal_signatures.py resuelve llamadas pyxel.*
         │
    ┌────▼──────────┐
    │ ASSET BAKER   │  baker.py → assets_gen.c / assets_gen.h
    └────┬──────────┘  solo se activa si hay pyxel.load()
         │
    ┌────▼──────────┐
    │   TOOLCHAIN   │  targets/*.py invocan cc65 / zcc
    └────┬──────────┘  empaquetan el binario final
         │
   .prg / .com / .tap
```

---

## Etapa 1 — Frontend

### Entrada
Archivo `.py` del usuario.

### Herramienta
Módulo estándar `ast` de Python. No hay parser propio.

```python
import ast
tree = ast.parse(source_code)
```

### Responsabilidad: `frontend/validator.py`

`ast.NodeVisitor` que recorre el árbol y lanza `TranspilerError` ante cualquier
construcción fuera del subconjunto. Errores con número de línea y mensaje claro:

```
ERROR line 42: 'try/except' is not supported in this subset
ERROR line 17: class inheritance is not allowed — 'class B(A)' found
ERROR line  8: float literal '3.14' is not supported — use integer arithmetic
ERROR line 31: nested function definition is not allowed
```

El validador también detecta y registra las directivas de compilación:
- `pyxel.load(...)` → marca assets para el baker
- `@pyxel.config(...)` → extrae parámetros del game loop
- `pyxel.run(...)` / `pyxel.run_custom(...)` → determina modo de game loop

### Salida
AST Python estándar, validado. Las directivas de compilación se anotan como
metadata en el árbol pero no se eliminan aún (eso ocurre en el backend).

---

## Etapa 2 — Análisis

### Responsabilidad: `frontend/type_inference.py`

Segundo `ast.NodeVisitor` que recorre el AST validado y construye:

**Tabla de símbolos** — una por scope (global + una por función):

```python
@dataclass
class Symbol:
    name:    str
    type:    str          # 'int', 'bool', 'str', nombre de clase, 'list:int', ...
    scope:   str          # 'global', nombre de función
    kind:    str          # 'variable', 'parameter', 'function'
    const:   bool = False
```

**Registro de clases:**

```python
@dataclass
class ClassDef:
    name:    str
    fields:  dict[str, str]   # nombre → tipo
    methods: dict[str, FunctionSignature]
```

### Reglas de inferencia

- Literal entero → `int`
- Literal bool → `bool`
- Literal string → `str`
- `[...] * N` → `list:T` donde T se infiere del elemento
- `ClassName(...)` → tipo `ClassName`
- `a + b` donde ambos son `int` → `int`
- Llamada a función → tipo de retorno de la función (inferido recursivamente)

Si la inferencia falla, se emite un error pidiendo anotación explícita:

```
ERROR line 15: cannot infer type of 'result' — add type annotation: result: int = ...
```

### Salida
AST anotado: cada nodo `Name`, `Assign` y `FunctionDef` lleva su tipo resuelto
como atributo adicional. Tabla de símbolos y registro de clases disponibles para
el backend.

---

## Etapa 3 — Backend (generador de código C89)

### Responsabilidad: `backend/codegen.py`

Tercer `ast.NodeVisitor` que emite C89. Opera sobre el AST anotado.

### Correspondencia de nodos

| Nodo AST Python | Salida C89 |
|---|---|
| `Module` | archivo `.c` completo con includes y `main()` |
| `FunctionDef` | `tipo nombre(params) { decls; stmts; }` |
| `ClassDef` | `typedef struct {...} Nombre;` + funciones `Nombre_*` |
| `If` | `if (...) { ... } else if (...) { ... } else { ... }` |
| `While` | `while (...) { ... }` |
| `For` + `range` | `for (i = start; i < stop; i += step) { ... }` |
| `Assign` | asignación (declaración en pre-scan del scope) |
| `AugAssign` | `+=`, `-=`, etc. |
| `Return` | `return expr;` |
| `Call` a pyxel.* | `hal_nombre(args)` — resuelto via hal_signatures.py |
| `Call` a función propia | `nombre(args)` |
| `Call` a `pyxel.load()` | **eliminado** — manejado por asset baker |
| `Attribute` (`self.x`) | `self->x` si es puntero, `self.x` si es por valor |

### Pre-scan de scope (obligatorio para C89)

C89 requiere que todas las declaraciones de variables estén al inicio del bloque.
El generador hace un pre-scan de cada función para recopilar todas las variables
locales y emitirlas antes de las instrucciones:

```c
int fibonacci(int n) {
    /* declaraciones al inicio — generadas por pre-scan */
    int a;
    int b;
    int tmp;
    int i;
    /* instrucciones */
    a = 0;
    b = 1;
    ...
}
```

### Resolución de métodos de clase

`v.add(other)` donde `v` es de tipo `Vector` → `Vector_add(&v, &other)`

El generador consulta el registro de clases para saber el tipo de `v` y construye
el nombre de la función C correspondiente.

### Responsabilidad: `backend/hal_signatures.py`

Diccionario que mapea cada llamada `pyxel.*` a su equivalente HAL en C:

```python
HAL_SIGNATURES = {
    "pyxel.cls":    ("hal_cls",    ["int"]),
    "pyxel.pset":   ("hal_pset",   ["int", "int", "int"]),
    "pyxel.line":   ("hal_line",   ["int", "int", "int", "int", "int"]),
    "pyxel.rect":   ("hal_rect",   ["int", "int", "int", "int", "int"]),
    "pyxel.rectb":  ("hal_rectb",  ["int", "int", "int", "int", "int"]),
    "pyxel.circ":   ("hal_circ",   ["int", "int", "int", "int"]),
    "pyxel.circb":  ("hal_circb",  ["int", "int", "int", "int"]),
    "pyxel.blt":    ("hal_blt",    ["int", "int", "int", "int", "int", "int", "int"]),
    "pyxel.bltm":   ("hal_bltm",   ["int", "int", "int", "int", "int", "int", "int"]),
    "pyxel.text":   ("hal_text",   ["int", "int", "str", "int"]),
    "pyxel.btn":    ("hal_btn",    ["int"]),
    "pyxel.btnp":   ("hal_btnp",   ["int"]),
    "pyxel.play":   ("hal_play",   ["int", "int"]),
    "pyxel.stop":   ("hal_stop",   ["int"]),
    "pyxel.quit":   ("hal_quit",   []),
    # directivas — no generan código C
    "pyxel.init":   None,
    "pyxel.load":   None,
    "pyxel.run":    None,
    "pyxel.run_custom": None,
}
```

### Salida
Uno o más archivos `.c` y `.h` listos para compilar con cc65 o zcc.
Un archivo por módulo lógico: `main.c`, `assets_gen.c` (si hay assets).

---

## Etapa 4 — Asset Baker

### Responsabilidad: `assets/baker.py`

Se activa cuando el validador encontró una o más llamadas `pyxel.load()`.

### Proceso

1. Abre el `.pyxres` (es un ZIP estándar internamente)
2. Extrae los bancos de imagen (formato raw de Pyxel: 1 byte por pixel, índice de paleta 0-15)
3. Extrae los tilemaps (arrays de índices de tile)
4. Extrae las definiciones de sonido
5. Aplica la tabla de paleta del target (`assets/palette_maps.py`)
6. Emite `assets_gen.c` y `assets_gen.h`

### Formato de salida

```c
/* assets_gen.h — generado automáticamente, no editar */
#ifndef ASSETS_GEN_H
#define ASSETS_GEN_H

extern const unsigned char IMG_BANK_0[128*128];
extern const unsigned char TILEMAP_0[32*32];
extern const unsigned char SOUND_0_NOTES[];
extern const unsigned char SOUND_0_TONES[];
extern const unsigned char SOUND_0_VOLUMES[];
extern const unsigned int  SOUND_0_LENGTH;

#endif
```

### Responsabilidad: `assets/palette_maps.py`

Tabla de mapeado de los 16 colores de Pyxel a los colores nativos de cada target:

```python
PALETTE_PYXEL = [
    0x000000, 0x2b335f, 0x7e2072, 0x19959c,  # 0-3
    0x8b4852, 0x395c98, 0xa9c1ff, 0xeeeeee,  # 4-7
    0xd4186c, 0xd38441, 0xe9c35b, 0x70c6a9,  # 8-11
    0x7696de, 0xa3a3a3, 0xff9798, 0xedc7b0,  # 12-15
]

PALETTE_MAP = {
    "c64": [0, 6, 4, 3, 2, 6, 15, 1, 10, 8, 7, 5, 14, 12, 13, 9],
    "zx":  [0, 1, 2, 3, 4, 5, 6,  7, 0,  9, 2, 3,  4,  5,  6, 7],
}
```

---

## Etapa 5 — Toolchain

### Responsabilidad: `targets/base.py`

Clase abstracta que define la interfaz de cada target:

```python
class BaseTarget:
    def compile(self, c_files: list[str], output: str) -> bool: ...
    def package(self, binary: str, output: str) -> bool: ...
    def hal_include_path(self) -> str: ...
    def validate_config(self, config: dict) -> list[str]: ...  # retorna warnings
```

### Implementaciones

**`targets/c64.py`** — usa `cl65` (parte de cc65):
```
cl65 -t c64 -O -o game.prg main.c assets_gen.c ../../hal/c64/graphics.c ...
```

**`targets/cpm.py`** — usa `zcc` (z88dk):
```
zcc +cpm -O2 -o game.com main.c assets_gen.c ../../hal/cpm/...
```

**`targets/zx_spectrum.py`** — usa `zcc` (z88dk):
```
zcc +zx -O2 -o game_zx.bin main.c assets_gen.c ../../hal/zx/...
appmake +zx --binfile game_zx.bin --org 32768 -o game.tap
```
