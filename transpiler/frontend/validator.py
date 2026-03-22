"""
Stage 1 — Frontend validator.

Recorre el AST con ast.NodeVisitor y rechaza cualquier construcción
fuera del subconjunto soportado.  También extrae las directivas de
compilación (pyxel.init, pyxel.run, pyxel.load, @pyxel.config).
"""

import ast
from dataclasses import dataclass, field
from typing import Optional


class TranspilerError(Exception):
    pass


@dataclass
class CompileDirectives:
    width: int = 160
    height: int = 120
    fps: int = 50
    load_files: list = field(default_factory=list)
    game_loop_mode: str = "AUTO"   # AUTO | CONFIGURED | CUSTOM
    update_fn: Optional[str] = None
    draw_fn: Optional[str] = None
    custom_fn: Optional[str] = None
    config: dict = field(default_factory=dict)


class SubsetValidator(ast.NodeVisitor):
    def __init__(self):
        self._errors: list[str] = []
        self.directives = CompileDirectives()
        self._fn_depth = 0    # para detectar funciones anidadas
        self._in_class = False

    # ── Herramienta interna ───────────────────────────────────────────────

    def _err(self, node, msg: str):
        lineno = getattr(node, "lineno", "?")
        self._errors.append(f"ERROR line {lineno:>3}: {msg}")

    def validate(self, tree: ast.Module) -> CompileDirectives:
        self.visit(tree)
        if self._errors:
            raise TranspilerError("\n".join(self._errors))
        return self.directives

    # ── Imports ───────────────────────────────────────────────────────────

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name != "pyxel":
                self._err(node, f"'import {alias.name}' not allowed — only 'import pyxel'")

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._err(node, "'from ... import' is not supported")

    # ── Construcciones prohibidas ─────────────────────────────────────────

    def visit_Try(self, node):
        self._err(node, "'try/except' is not supported in this subset")

    def visit_TryStar(self, node):
        self._err(node, "'try/except*' is not supported in this subset")

    def visit_Raise(self, node):
        self._err(node, "'raise' is not supported")

    def visit_With(self, node):
        self._err(node, "'with' / context managers are not supported")

    def visit_AsyncFunctionDef(self, node):
        self._err(node, "async functions are not supported")

    def visit_AsyncFor(self, node):
        self._err(node, "'async for' is not supported")

    def visit_AsyncWith(self, node):
        self._err(node, "'async with' is not supported")

    def visit_Yield(self, node):
        self._err(node, "'yield' / generators are not supported")

    def visit_YieldFrom(self, node):
        self._err(node, "'yield from' is not supported")

    def visit_Lambda(self, node):
        self._err(node, "'lambda' is not supported")

    def visit_ListComp(self, node):
        self._err(node, "list comprehensions are not supported — rewrite with 'for'")

    def visit_DictComp(self, node):
        self._err(node, "dict comprehensions are not supported")

    def visit_SetComp(self, node):
        self._err(node, "set comprehensions are not supported")

    def visit_GeneratorExp(self, node):
        self._err(node, "generator expressions are not supported")

    def visit_Set(self, node):
        self._err(node, "sets are not supported")

    def visit_Nonlocal(self, node):
        self._err(node, "'nonlocal' is not supported")

    def visit_Delete(self, node):
        self._err(node, "'del' is not supported")

    def visit_Assert(self, node):
        self._err(node, "'assert' is not supported — no runtime error handling in target")

    def visit_JoinedStr(self, node):
        self._err(node, "f-strings are not supported — use string literals")

    # ── Literales float ───────────────────────────────────────────────────

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, float):
            self._err(node, f"float literal '{node.value}' is not supported — use integer arithmetic")

    # ── Clases ────────────────────────────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.bases:
            base_name = ast.unparse(node.bases[0]) if hasattr(ast, "unparse") else "?"
            self._err(node, f"class inheritance is not allowed — 'class {node.name}({base_name})' found")
            return
        for dec in node.decorator_list:
            self._err(node, f"class decorators are not supported on 'class {node.name}'")
        old = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = old

    # ── Funciones ─────────────────────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Funciones anidadas (closures) — solo permitidas dentro de clases
        if self._fn_depth > 0 and not self._in_class:
            self._err(node, f"nested function definition is not allowed — '{node.name}'")
            return

        # Decoradores: solo @pyxel.config está permitido
        for dec in node.decorator_list:
            if self._is_pyxel_config(dec):
                self._extract_config(dec, node.name)
            else:
                self._err(node, f"decorators are not supported (except @pyxel.config) on '{node.name}'")

        # Argumentos prohibidos
        args = node.args
        if args.vararg:
            self._err(node, f"'*args' is not supported in '{node.name}'")
        if args.kwarg:
            self._err(node, f"'**kwargs' is not supported in '{node.name}'")
        if args.kwonlyargs:
            self._err(node, f"keyword-only parameters are not supported in '{node.name}'")
        if args.posonlyargs:
            self._err(node, f"positional-only parameters are not supported in '{node.name}'")

        # Valores por defecto: solo literales constantes
        for default in args.defaults:
            if not isinstance(default, (ast.Constant,)):
                # Permitimos -N (UnaryOp con USub)
                if not (isinstance(default, ast.UnaryOp) and isinstance(default.op, ast.USub)):
                    self._err(node, f"default values must be literal constants in '{node.name}'")

        self._fn_depth += 1
        self.generic_visit(node)
        self._fn_depth -= 1

    # ── Bucles ────────────────────────────────────────────────────────────

    def visit_For(self, node: ast.For):
        if not (isinstance(node.iter, ast.Call) and
                isinstance(node.iter.func, ast.Name) and
                node.iter.func.id == "range"):
            self._err(node, "only 'for i in range(...)' is supported — no iteration over objects")
        self.generic_visit(node)

    # ── Llamadas de nivel sentencia (directivas de compilación) ───────────

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "pyxel":
                    attr = func.attr
                    if attr == "init":
                        self._extract_init(call)
                    elif attr == "run":
                        self._extract_run(call)
                    elif attr == "run_custom":
                        self._extract_run_custom(call)
                    elif attr == "load":
                        self._extract_load(call)
        self.generic_visit(node)

    # ── Helpers directivas ────────────────────────────────────────────────

    def _is_pyxel_config(self, node) -> bool:
        return (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == "pyxel" and
                node.func.attr == "config")

    def _extract_init(self, call: ast.Call):
        if len(call.args) >= 2:
            w, h = call.args[0], call.args[1]
            if isinstance(w, ast.Constant) and isinstance(w.value, int):
                self.directives.width = w.value
            if isinstance(h, ast.Constant) and isinstance(h.value, int):
                self.directives.height = h.value
        # fps como keyword
        for kw in call.keywords:
            if kw.arg == "fps" and isinstance(kw.value, ast.Constant):
                self.directives.fps = kw.value.value

    def _extract_run(self, call: ast.Call):
        if len(call.args) >= 2:
            a0, a1 = call.args[0], call.args[1]
            if isinstance(a0, ast.Name):
                self.directives.update_fn = a0.id
            if isinstance(a1, ast.Name):
                self.directives.draw_fn = a1.id
        if self.directives.game_loop_mode != "CONFIGURED":
            self.directives.game_loop_mode = "AUTO"

    def _extract_run_custom(self, call: ast.Call):
        if call.args and isinstance(call.args[0], ast.Name):
            self.directives.custom_fn = call.args[0].id
        self.directives.game_loop_mode = "CUSTOM"

    def _extract_load(self, call: ast.Call):
        if call.args and isinstance(call.args[0], ast.Constant):
            self.directives.load_files.append(call.args[0].value)

    def _extract_config(self, dec_call: ast.Call, fn_name: str):
        self.directives.game_loop_mode = "CONFIGURED"
        config = {}
        for kw in dec_call.keywords:
            if isinstance(kw.value, ast.Constant):
                config[kw.arg] = kw.value.value
        self.directives.config = config


# ── API pública ───────────────────────────────────────────────────────────────

def validate(source: str) -> tuple[ast.Module, CompileDirectives]:
    """Parsea y valida el subconjunto.  Devuelve (AST, directivas)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise TranspilerError(f"ERROR: syntax error — {e}")
    v = SubsetValidator()
    directives = v.validate(tree)
    return tree, directives
