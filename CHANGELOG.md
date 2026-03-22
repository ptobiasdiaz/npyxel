# Changelog

All notable changes to this project will be documented in this file.

## [0.0.1] - 2026-03-22

### Added

- **Player (`npyxel play`)** — desarrollo iterativo sin compilación:
  - Valida el subconjunto Python soportado antes de lanzar
  - Ejecuta el script directamente sobre Pyxel (assets y paleta originales)
  - Salida clara en consola: errores de subconjunto con número de línea
  - Flag `--target` parseado y preparado para futura conversión de paleta
- **Frontend / Validator** (`transpiler/frontend/validator.py`) — detecta construcciones fuera del subconjunto soportado
- **Frontend / Type inference** (`transpiler/frontend/type_inference.py`) — inferencia de tipos estática y tabla de símbolos
- **Ejemplos** en `examples/`: `hello.py`, `pong.py`

### Architecture

- Estructura de paquetes establecida: `transpiler/`, `hal/`, `docs/`, `examples/`
- Especificaciones completas en `docs/` (01_subset … 09_player)
- Diseño agnóstico al target: añadir una máquina nueva no requiere cambios en el core

### Not yet included

- Generación de código C89 (`transpiler/backend/codegen.py`)
- Asset baker (`transpiler/assets/baker.py`)
- Soporte de targets (`transpiler/targets/`)
- HAL por máquina (`hal/*/`)
- Selección de target en el player (`--target`)
- Empaquetado como comando `npyxel` instalable (por ahora: `python -m transpiler.preview`)
