"""
Stage 2 — Inferencia de tipos y tabla de símbolos.

Construye:
  - SymbolTable  — una entrada por variable/parámetro/función, por scope
  - ClassRegistry — campos y métodos de cada clase definida
  - node_types    — dict id(nodo) -> tipo C  (para que codegen no repita inferencia)
"""

import ast
from dataclasses import dataclass, field
from typing import Optional

from transpiler.frontend.validator import CompileDirectives, TranspilerError


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class Symbol:
    name: str
    type: str        # 'int', 'bool', 'str', 'void', 'list:int', nombre de clase…
    scope: str       # 'global' | nombre de función | 'ClassName.__init__'
    kind: str        # 'variable' | 'parameter' | 'function'
    const: bool = False


@dataclass
class FunctionSignature:
    name: str
    params: list     # lista de (nombre, tipo_python)
    return_type: str


@dataclass
class ClassRecord:
    name: str
    fields: dict = field(default_factory=dict)   # nombre -> tipo_python
    methods: dict = field(default_factory=dict)  # nombre -> FunctionSignature


class SymbolTable:
    def __init__(self):
        self._scopes: dict[str, dict[str, Symbol]] = {"global": {}}
        self.current_scope: str = "global"

    def enter_scope(self, name: str):
        self._scopes.setdefault(name, {})
        self.current_scope = name

    def exit_scope(self):
        self.current_scope = "global"

    def define(self, sym: Symbol):
        self._scopes.setdefault(sym.scope, {})[sym.name] = sym

    def lookup(self, name: str, scope: Optional[str] = None) -> Optional[Symbol]:
        s = scope or self.current_scope
        sym = self._scopes.get(s, {}).get(name)
        if sym:
            return sym
        return self._scopes.get("global", {}).get(name)

    def scope_symbols(self, scope: str) -> dict[str, Symbol]:
        return self._scopes.get(scope, {})


# ── Inferidor ─────────────────────────────────────────────────────────────────

_BUILTINS_RETURN = {
    "len": "int",
    "abs": "int",
    "min": "int",
    "max": "int",
    "range": "range",
    "print": "void",
}

_PYXEL_RETURN = {
    "btn": "bool", "btnp": "bool", "btnr": "bool",
    "pget": "int", "frame_count": "int",
    "width": "int", "height": "int", "fps": "int",
}


class TypeInferrer(ast.NodeVisitor):
    def __init__(self, directives: CompileDirectives):
        self.directives = directives
        self.symbols = SymbolTable()
        self.classes: dict[str, ClassRecord] = {}
        self.functions: dict[str, FunctionSignature] = {}
        self._current_class: Optional[str] = None
        self._errors: list[str] = []
        self.node_types: dict[int, str] = {}  # id(node) -> tipo

    # ── API pública ───────────────────────────────────────────────────────

    def infer(self, tree: ast.Module):
        """Primer pase: recopilar firmas.  Segundo pase: anotar tipos."""
        self._first_pass(tree)
        self.visit(tree)
        if self._errors:
            raise TranspilerError("\n".join(self._errors))
        return self.symbols, self.classes, self.node_types

    # ── Primer pase: recopilar firmas de clases y funciones ───────────────

    def _first_pass(self, tree: ast.Module):
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                self._collect_class(stmt)
            elif isinstance(stmt, ast.FunctionDef):
                self._collect_function(stmt)

    def _collect_class(self, node: ast.ClassDef):
        rec = ClassRecord(name=node.name)
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                sig = self._build_sig(item, class_name=node.name)
                rec.methods[item.name] = sig
                if item.name == "__init__":
                    self._extract_init_fields(item, rec)
        self.classes[node.name] = rec

    def _extract_init_fields(self, node: ast.FunctionDef, rec: ClassRecord):
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    if (isinstance(t, ast.Attribute) and
                            isinstance(t.value, ast.Name) and
                            t.value.id == "self" and
                            t.attr not in rec.fields):
                        rec.fields[t.attr] = self._infer_expr(stmt.value, scope="global")
            elif isinstance(stmt, ast.AnnAssign):
                if (isinstance(stmt.target, ast.Attribute) and
                        isinstance(stmt.target.value, ast.Name) and
                        stmt.target.value.id == "self"):
                    rec.fields[stmt.target.attr] = self._ann_to_type(stmt.annotation)

    def _collect_function(self, node: ast.FunctionDef):
        sig = self._build_sig(node, class_name=None)
        self.functions[node.name] = sig
        self.symbols.define(Symbol(
            name=node.name,
            type=f"fn:{sig.return_type}",
            scope="global",
            kind="function",
        ))

    def _build_sig(self, node: ast.FunctionDef, class_name: Optional[str]) -> FunctionSignature:
        args = node.args.args
        if class_name and args:
            args = args[1:]  # saltar self
        params = []
        for arg in args:
            typ = self._ann_to_type(arg.annotation) if arg.annotation else "int"
            params.append((arg.arg, typ))
        ret = self._ann_to_type(node.returns) if node.returns else self._guess_return(node)
        return FunctionSignature(name=node.name, params=params, return_type=ret)

    def _guess_return(self, node: ast.FunctionDef) -> str:
        for n in ast.walk(node):
            if isinstance(n, ast.Return) and n.value is not None:
                return "int"  # aproximación conservadora
        return "void"

    # ── Segundo pase: anotar nodos ────────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        old = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old

    def visit_FunctionDef(self, node: ast.FunctionDef):
        scope_name = (f"{self._current_class}.{node.name}"
                      if self._current_class else node.name)
        self.symbols.enter_scope(scope_name)

        # Registrar parámetros en el scope
        args = node.args.args
        start = 1 if self._current_class and args else 0
        cls_name = self._current_class
        sig_key = node.name
        if cls_name:
            rec = self.classes.get(cls_name)
            sig = rec.methods.get(sig_key) if rec else None
        else:
            sig = self.functions.get(sig_key)

        if sig:
            for (pname, ptype) in sig.params:
                self.symbols.define(Symbol(
                    name=pname, type=ptype,
                    scope=scope_name, kind="parameter",
                ))

        self.generic_visit(node)
        self.symbols.exit_scope()

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)
        typ = self._infer_expr(node.value)
        self.node_types[id(node)] = typ
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.node_types[id(target)] = typ
                self.symbols.define(Symbol(
                    name=target.id, type=typ,
                    scope=self.symbols.current_scope,
                    kind="variable",
                ))

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.generic_visit(node)
        typ = self._ann_to_type(node.annotation)
        self.node_types[id(node)] = typ
        if isinstance(node.target, ast.Name):
            self.node_types[id(node.target)] = typ
            self.symbols.define(Symbol(
                name=node.target.id, type=typ,
                scope=self.symbols.current_scope,
                kind="variable",
            ))

    # ── Inferencia de expresiones ─────────────────────────────────────────

    def _infer_expr(self, node, scope: Optional[str] = None) -> str:
        if node is None:
            return "void"

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, str):
                return "str"
            return "int"

        if isinstance(node, ast.Name):
            if node.id in ("True", "False"):
                return "bool"
            if node.id == "None":
                return "void"
            sym = self.symbols.lookup(node.id, scope)
            if sym:
                return sym.type
            if node.id in _BUILTINS_RETURN:
                return _BUILTINS_RETURN[node.id]
            if node.id in self.classes:
                return node.id
            return "int"

        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "pyxel":
                return _PYXEL_RETURN.get(node.attr, "void")
            # self.field
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                cls = self.classes.get(self._current_class or "")
                if cls and node.attr in cls.fields:
                    return cls.fields[node.attr]
            return "int"

        if isinstance(node, ast.BinOp):
            lt = self._infer_expr(node.left, scope)
            rt = self._infer_expr(node.right, scope)
            if lt == "str" or rt == "str":
                return "str"
            return "int"

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return "bool"
            return self._infer_expr(node.operand, scope)

        if isinstance(node, ast.BoolOp):
            return "bool"

        if isinstance(node, ast.Compare):
            return "bool"

        if isinstance(node, ast.List):
            elem = self._infer_expr(node.elts[0], scope) if node.elts else "int"
            return f"list:{elem}"

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            # [x] * N  → list
            if isinstance(node.left, ast.List):
                elem = self._infer_expr(node.left.elts[0], scope) if node.left.elts else "int"
                return f"list:{elem}"

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in _BUILTINS_RETURN:
                    return _BUILTINS_RETURN[func.id]
                if func.id in self.classes:
                    return func.id
                if func.id in self.functions:
                    return self.functions[func.id].return_type
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == "pyxel":
                    return _PYXEL_RETURN.get(func.attr, "void")
                # método de clase
                obj_type = self._infer_expr(func.value, scope)
                if obj_type in self.classes:
                    rec = self.classes[obj_type]
                    sig = rec.methods.get(func.attr)
                    if sig:
                        return sig.return_type
            return "int"

        if isinstance(node, ast.Subscript):
            val_type = self._infer_expr(node.value, scope)
            if val_type.startswith("list:"):
                return val_type[5:]
            return "int"

        if isinstance(node, ast.IfExp):
            return self._infer_expr(node.body, scope)

        return "int"

    # ── Conversión de anotación a tipo ────────────────────────────────────

    def _ann_to_type(self, ann) -> str:
        if ann is None:
            return "int"
        if isinstance(ann, ast.Name):
            return {"int": "int", "bool": "bool", "str": "str",
                    "None": "void", "list": "list:int"}.get(ann.id, ann.id)
        if isinstance(ann, ast.Constant) and ann.value is None:
            return "void"
        if isinstance(ann, ast.Subscript):
            # list[int] etc.
            if isinstance(ann.value, ast.Name) and ann.value.id == "list":
                inner = self._ann_to_type(ann.slice)
                return f"list:{inner}"
        return "int"


# ── API pública ───────────────────────────────────────────────────────────────

def infer_types(tree: ast.Module, directives: CompileDirectives):
    """Devuelve (SymbolTable, clases, node_types)."""
    inferrer = TypeInferrer(directives)
    return inferrer.infer(tree)
