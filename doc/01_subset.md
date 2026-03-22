# Subconjunto Python soportado

## Principio general

El subconjunto es **estático y tipable localmente**. Toda construcción debe ser
traducible a C89 de forma mecánica y predecible, sin análisis global ni resolución
dinámica de nombres en runtime.

---

## ✅ Control de flujo

```python
if condition:
    ...
elif other:
    ...
else:
    ...

while condition:
    ...

for i in range(n):          # solo range() — sin iteración sobre objetos arbitrarios
    ...

for i in range(start, stop):
    ...

for i in range(start, stop, step):
    ...

break
continue
return value
return          # return implícito None → void en C
```

---

## ✅ Funciones

```python
def name(a, b, c):          # parámetros posicionales únicamente
    ...

def name(a, b=10):          # valores por defecto permitidos si son literales constantes
    ...

global x                    # permitido para acceso a variables globales
```

**No permitido:**
- `*args`, `**kwargs`
- Parámetros solo-keyword (`def f(*, x)`)
- Funciones anidadas (closures)
- `lambda`
- Decoradores (excepto `@pyxel.config` que es una directiva de compilación)

---

## ✅ Clases (sin herencia)

```python
class MyClass:
    def __init__(self, x, y):
        self.x = x              # atributos SOLO definidos en __init__
        self.y = y

    def my_method(self, other):
        return self.x + other

    def __str__(self):          # opcional, para print()
        return "..."
```

**Reglas estrictas:**
- Sin herencia (`class B(A)` → error)
- Sin `super()`
- Sin atributos de clase (solo de instancia)
- Sin atributos creados fuera de `__init__`
- Sin `@property`, `@classmethod`, `@staticmethod`
- Sin polimorfismo dinámico

**Transpilación:**
```c
typedef struct { int x; int y; } MyClass;
MyClass MyClass_new(int x, int y) { ... }
int MyClass_my_method(MyClass *self, int other) { ... }
```

---

## ✅ Tipos de datos

| Tipo Python | Tipo C89 generado | Notas |
|---|---|---|
| `int` | `int` (16 bits en target) | Rango: -32768 a 32767 |
| `bool` | `unsigned char` | 0 / 1 |
| `str` | `const char*` | Solo literales estáticos |
| lista `[...]` | array estático | Tamaño debe ser conocido en compilación |
| instancia de clase | struct por valor o puntero | Ver docs/02_pipeline.md |

**`float` no está soportado.** El hardware de 8 bits no tiene FPU y la emulación
software es demasiado costosa. Usar aritmética entera escalada si es necesario.

---

## ✅ Operadores

```python
# Aritméticos
+ - * // %  **

# Comparación
== != < > <= >=

# Lógicos
and  or  not

# Bit a bit — especialmente útiles en targets de 8 bits
& | ^ ~ << >>

# Asignación compuesta
+= -= *= //= %= &= |= ^= <<= >>=
```

---

## ✅ Estructuras de datos

### Listas
```python
data = [0, 1, 2, 3]             # lista literal → array estático
data = [0] * 64                 # array de tamaño fijo → int data[64] = {0}
data[i] = value                 # indexación permitida
x = data[i]
n = len(data)                   # len() de lista → constante en compilación
```

El tamaño debe ser determinable en tiempo de compilación. Listas de tamaño
dinámico no están soportadas.

### Diccionarios (soporte limitado)
```python
d = {0: 10, 1: 20, 2: 30}      # solo claves enteras literales → array indexado
d = {"a": 1, "b": 2}           # claves string literales → enum + array
```

Diccionarios con claves dinámicas no están soportados.

---

## ✅ Built-ins permitidos

```python
len(x)          # solo sobre listas de tamaño estático
range(...)      # solo en for
print(x)        # emite a la salida estándar del target (hal_print)
abs(x)          # valor absoluto entero
min(a, b)       # mínimo de dos valores
max(a, b)       # máximo de dos valores
```

---

## ❌ Explícitamente no soportado

| Construcción | Razón |
|---|---|
| `float` | Sin FPU en 8 bits |
| `try / except / finally` | Sin gestión de excepciones en el target |
| Herencia de clases | Demasiado overhead, vtables incompatibles |
| `yield` / generadores | Requiere coroutines |
| Closures / funciones anidadas | Difícil de representar en C89 |
| `lambda` | Azúcar sintáctico de closures |
| `import` (excepto `import pyxel`) | Sin sistema de módulos en runtime |
| Strings dinámicos | Sin heap generoso |
| `list.sort()`, `sorted()` | Coste impredecible en 8 bits |
| `dict` con claves dinámicas | Sin hash table en target |
| `*args` / `**kwargs` | Sin stack de argumentos dinámico |
| Comprensiones de lista | Se pueden reescribir con `for` |
| `with` / context managers | Sin RAII en C89 |
| `assert` | Sin manejo de errores en runtime |
| `global` en clases | No tiene sentido semántico aquí |

---

## Anotaciones de tipo

Cuando la inferencia de tipos no pueda resolver el tipo de una variable, el
transpilador lo indicará con un error y pedirá una anotación explícita PEP 526:

```python
x: int = some_function()
items: list = [0] * 32
```

Las anotaciones son opcionales cuando el tipo es inferible, obligatorias cuando no lo es.
