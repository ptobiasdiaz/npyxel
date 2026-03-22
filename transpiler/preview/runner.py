"""Orquesta validación, (baker preview) y lanzamiento del script con Pyxel."""

import sys
from pathlib import Path

from transpiler.frontend.validator import validate, TranspilerError
from transpiler.frontend.type_inference import infer_types
from transpiler.preview import reporter
from transpiler.preview.patcher import patch_load


def run(script_path: Path, target: str | None = None):
    source = script_path.read_text(encoding="utf-8")

    # ── Etapa 1: validación de subconjunto ───────────────────────────────
    try:
        tree, directives = validate(source)
    except TranspilerError as e:
        reporter.show_errors("Subset validation failed:", str(e))
        sys.exit(1)
    reporter.ok("Subset validation passed")

    # ── Etapa 2: inferencia de tipos ─────────────────────────────────────
    try:
        infer_types(tree, directives)
    except TranspilerError as e:
        reporter.show_errors("Type inference failed:", str(e))
        sys.exit(1)
    reporter.ok("Type inference passed")

    # ── Etapa 3: patch de assets (sin target → no-op) ────────────────────
    patch_load(target)

    # ── Etapa 4: lanzar el script con Pyxel ─────────────────────────────
    target_label = f" ({target} palette)" if target else ""
    reporter.launch(f"Launching{target_label}...")

    script_globals = {
        "__name__": "__main__",
        "__file__": str(script_path.resolve()),
    }
    try:
        exec(compile(source, str(script_path), "exec"), script_globals)
    except SystemExit:
        pass
