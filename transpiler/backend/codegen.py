"""
Stage 3 — Generador de código C89.

Recorre el AST anotado y emite un archivo .c completo.
El game loop / main() se genera por separado en targets/*.py
"""

import ast
from typing import Optional

from transpiler.backend.hal_signatures import HAL_SIGNATURES, KEY_CONSTANTS
from transpiler.frontend.validator import CompileDirectives

_INDENT = "    "


# ── Utilidades de tipos ───────────────────────────────────────────────────────

def _py_type_to_c(typ: str, classes: dict) -> str:
    mapping = {
        "int": "int",
        "bool": "unsigned char",
        "str": "const char*",
        "void": "void",
    }
    if typ in mapping:
        return mapping[typ]
    if typ.startswith("list:"):
        elem = _py_type_to_c(typ[5:], classes)
        return f"{elem}*"
    if typ in classes:
        return typ
    if typ.startswith("fn:"):
        return "void"
    return "int"


# ── Generador principal ───────────────────────────────────────────────────────

class CodeGenerator(ast.NodeVisitor):

    def __init__(self, symbols, classes: dict, node_types: dict,
                 directives: CompileDirectives, key_include: str = ""):
        self.symbols = symbols
        self.classes = classes
        self.node_types = node_types
        self.directives = directives
        self._key_include = key_include

        self._indent = 0
        self._lines: list[str] = []
        self._current_fn: Optional[str] = None
        self._current_class: Optional[str] = None

        # scope_key -> {varname: c_type}  — calculado en pre-scan
        self._local_vars: dict[str, dict[str, str]] = {}

    # ── API pública ───────────────────────────────────────────────────────

    def generate(self, tree: ast.Module) -> str:
        self._prescan_all(tree)
        self.visit(tree)
        return "\n".join(self._lines)

    # ── Pre-scan de variables locales (obligatorio para C89) ─────────────

    def _prescan_all(self, tree: ast.Module):
        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                locs = {}
                self._scan_fn_body(stmt, locs)
                self._local_vars[stmt.name] = locs
            elif isinstance(stmt, ast.ClassDef):
                for item in stmt.body:
                    if isinstance(item, ast.FunctionDef):
                        key = f"{stmt.name}.{item.name}"
                        locs = {}
                        self._scan_fn_body(item, locs)
                        self._local_vars[key] = locs

    def _scan_fn_body(self, fn: ast.FunctionDef, out: dict):
        """Recopila todas las variables locales asignadas en el cuerpo."""
        # Variables declaradas 'global' en esta función → NO son locales
        globals_in_fn: set[str] = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Global):
                globals_in_fn.update(node.names)

        for node in ast.walk(fn):
            if node is fn:
                continue
            # No descender en funciones anidadas
            if isinstance(node, ast.FunctionDef) and node is not fn:
                continue
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id not in out and t.id not in globals_in_fn:
                        typ = self.node_types.get(id(t), "int")
                        c_type = _py_type_to_c(typ, self.classes)
                        out[t.id] = (c_type, typ)   # (c_type, py_type)
            elif isinstance(node, ast.AnnAssign):
                if (isinstance(node.target, ast.Name) and
                        node.target.id not in out and
                        node.target.id not in globals_in_fn):
                    typ = self.node_types.get(id(node.target), "int")
                    c_type = _py_type_to_c(typ, self.classes)
                    out[node.target.id] = (c_type, typ)
            elif isinstance(node, ast.For):
                if (isinstance(node.target, ast.Name) and
                        node.target.id not in out and
                        node.target.id not in globals_in_fn):
                    out[node.target.id] = ("int", "int")

    # ── Emisión de líneas ─────────────────────────────────────────────────

    def _emit(self, line: str = ""):
        self._lines.append(_INDENT * self._indent + line)

    # ── Conversión de expresiones AST → C ────────────────────────────────

    def _expr(self, node) -> str:
        if node is None:
            return ""
        if isinstance(node, ast.Constant):
            return self._const(node)
        if isinstance(node, ast.Name):
            return self._name(node.id)
        if isinstance(node, ast.Attribute):
            return self._attribute(node)
        if isinstance(node, ast.BinOp):
            return self._binop(node)
        if isinstance(node, ast.UnaryOp):
            return self._unaryop(node)
        if isinstance(node, ast.BoolOp):
            return self._boolop(node)
        if isinstance(node, ast.Compare):
            return self._compare(node)
        if isinstance(node, ast.Call):
            return self._call(node)
        if isinstance(node, ast.Subscript):
            return f"{self._expr(node.value)}[{self._expr(node.slice)}]"
        if isinstance(node, ast.List):
            elems = ", ".join(self._expr(e) for e in node.elts)
            return f"{{{elems}}}"
        if isinstance(node, ast.IfExp):
            t = self._expr(node.test)
            b = self._expr(node.body)
            o = self._expr(node.orelse)
            return f"({t} ? {b} : {o})"
        return "/* ?expr */"

    def _const(self, node: ast.Constant) -> str:
        v = node.value
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if v is None:
            return "0"
        return str(v)

    def _name(self, name: str) -> str:
        if name in KEY_CONSTANTS:
            return KEY_CONSTANTS[name]
        if name == "True":
            return "1"
        if name == "False":
            return "0"
        if name == "None":
            return "0"
        return name

    def _attribute(self, node: ast.Attribute) -> str:
        if isinstance(node.value, ast.Name) and node.value.id == "pyxel":
            attr = node.attr
            if attr in KEY_CONSTANTS:
                return KEY_CONSTANTS[attr]
            if attr == "width":
                return "PYXEL_WIDTH"
            if attr == "height":
                return "PYXEL_HEIGHT"
            if attr == "fps":
                return "PYXEL_FPS"
            if attr == "frame_count":
                return "hal_frame_count()"
            return f"/* pyxel.{attr} */"
        # self.field
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"self->{node.attr}"
        obj = self._expr(node.value)
        return f"{obj}.{node.attr}"

    def _binop(self, node: ast.BinOp) -> str:
        ops = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
            ast.FloorDiv: "/", ast.Mod: "%",
            ast.BitAnd: "&", ast.BitOr: "|", ast.BitXor: "^",
            ast.LShift: "<<", ast.RShift: ">>",
        }
        op_type = type(node.op)
        if op_type == ast.Pow:
            return f"hal_ipow({self._expr(node.left)}, {self._expr(node.right)})"
        op_str = ops.get(op_type, "?")
        return f"({self._expr(node.left)} {op_str} {self._expr(node.right)})"

    def _unaryop(self, node: ast.UnaryOp) -> str:
        ops = {ast.USub: "-", ast.UAdd: "+", ast.Not: "!", ast.Invert: "~"}
        op_str = ops.get(type(node.op), "?")
        return f"({op_str}{self._expr(node.operand)})"

    def _boolop(self, node: ast.BoolOp) -> str:
        op = "&&" if isinstance(node.op, ast.And) else "||"
        parts = [self._expr(v) for v in node.values]
        return f"({f' {op} '.join(parts)})"

    def _compare(self, node: ast.Compare) -> str:
        ops = {
            ast.Eq: "==", ast.NotEq: "!=",
            ast.Lt: "<", ast.Gt: ">",
            ast.LtE: "<=", ast.GtE: ">=",
        }
        left = self._expr(node.left)
        parts = [left]
        for op, cmp in zip(node.ops, node.comparators):
            parts.append(ops.get(type(op), "?"))
            parts.append(self._expr(cmp))
        return f"({' '.join(parts)})"

    def _call(self, node: ast.Call) -> str:
        func = node.func

        # pyxel.* calls
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "pyxel"):
            return self._pyxel_call(func.attr, node)

        # built-ins
        if isinstance(func, ast.Name):
            name = func.id
            if name == "len":
                arg = self._expr(node.args[0])
                return f"(sizeof({arg}) / sizeof({arg}[0]))"
            if name == "abs":
                return f"abs({self._expr(node.args[0])})"
            if name == "min":
                a, b = self._expr(node.args[0]), self._expr(node.args[1])
                return f"(({a}) < ({b}) ? ({a}) : ({b}))"
            if name == "max":
                a, b = self._expr(node.args[0]), self._expr(node.args[1])
                return f"(({a}) > ({b}) ? ({a}) : ({b}))"
            if name == "str":
                return f"hal_istr({self._expr(node.args[0])})"
            if name == "print":
                args = ", ".join(self._expr(a) for a in node.args)
                return f"hal_debug_print({args})"
            if name in self.classes:
                args = ", ".join(self._expr(a) for a in node.args)
                return f"{name}_new({args})"
            # llamada normal
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{name}({args})"

        # método de objeto
        if isinstance(func, ast.Attribute):
            obj_type = None
            if isinstance(func.value, ast.Name):
                sym = self.symbols.lookup(func.value.id)
                if sym:
                    obj_type = sym.type
            if obj_type and obj_type in self.classes:
                obj_ref = "&" + self._expr(func.value)
                args = ", ".join([obj_ref] + [self._expr(a) for a in node.args])
                return f"{obj_type}_{func.attr}({args})"
            obj = self._expr(func.value)
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{obj}.{func.attr}({args})"

        return "/* ?call */"

    def _pyxel_call(self, attr: str, node: ast.Call) -> str:
        sig = HAL_SIGNATURES.get(attr)
        if sig is None:
            return ""   # directiva — sin código

        hal_name, _ = sig
        args = list(node.args)
        kwargs = {kw.arg: kw.value for kw in node.keywords}

        if attr in ("blt", "bltm"):
            # colkey opcional — default -1
            args_c = [self._expr(a) for a in args]
            if "colkey" in kwargs:
                args_c.append(self._expr(kwargs["colkey"]))
            elif len(args_c) < 8:
                args_c.append("-1")
        elif attr == "btnp":
            args_c = [self._expr(a) for a in args]
            while len(args_c) < 3:
                args_c.append("0")
        else:
            args_c = [self._expr(a) for a in args]
            for kw in node.keywords:
                args_c.append(self._expr(kw.value))

        return f"{hal_name}({', '.join(args_c)})"

    # ── Helpers de firma de función ───────────────────────────────────────

    def _fn_ret_type(self, node: ast.FunctionDef, class_name: Optional[str] = None) -> str:
        if node.name == "__init__" and class_name:
            return class_name
        if node.returns:
            from transpiler.frontend.type_inference import TypeInferrer
            ann = node.returns
            if isinstance(ann, ast.Name):
                mapping = {"int": "int", "bool": "unsigned char",
                           "str": "const char*", "None": "void"}
                return mapping.get(ann.id, ann.id)
            return "void"
        # sin anotación: buscar return
        for n in ast.walk(node):
            if isinstance(n, ast.Return) and n.value is not None:
                return "int"
        return "void"

    def _fn_params_c(self, node: ast.FunctionDef,
                     is_method: bool, class_name: Optional[str]) -> list[str]:
        args = node.args.args
        params = []
        if is_method and class_name:
            params.append(f"{class_name}* self")
            args = args[1:]  # skip self

        for arg in args:
            if arg.annotation:
                ann = arg.annotation
                if isinstance(ann, ast.Name):
                    mapping = {"int": "int", "bool": "unsigned char",
                               "str": "const char*", "None": "void"}
                    ctype = mapping.get(ann.id, ann.id)
                else:
                    ctype = "int"
            else:
                ctype = "int"
            params.append(f"{ctype} {arg.arg}")

        return params if params else ["void"]

    def _fn_c_name(self, fn_name: str, class_name: Optional[str]) -> str:
        if class_name:
            if fn_name == "__init__":
                return f"{class_name}_new"
            return f"{class_name}_{fn_name}"
        return fn_name

    def _fn_signature_str(self, node: ast.FunctionDef,
                          is_method: bool, class_name: Optional[str]) -> str:
        ret = self._fn_ret_type(node, class_name)
        c_name = self._fn_c_name(node.name, class_name)
        params = ", ".join(self._fn_params_c(node, is_method, class_name))
        return f"{ret} {c_name}({params})"

    def _param_names(self, node: ast.FunctionDef) -> set[str]:
        return {arg.arg for arg in node.args.args}

    # ── Emit de declaraciones locales (pre-scan) ──────────────────────────

    def _emit_locals(self, scope_key: str, exclude: set[str]):
        locs = self._local_vars.get(scope_key, {})
        emitted = False
        for var_name, (c_type, py_type) in locs.items():
            if var_name in exclude:
                continue
            if c_type.endswith("*"):
                # Arrays: se declaran en el punto de asignación (ver visit_Assign)
                continue
            self._emit(f"{c_type} {var_name};")
            emitted = True
        if emitted:
            self._emit()

    # ── Visitors de sentencias ────────────────────────────────────────────

    def visit_Module(self, node: ast.Module):
        self._emit("/* Generated by pyxel-retro transpiler */")
        self._emit("/* DO NOT EDIT MANUALLY */")
        self._emit()
        self._emit('#include "hal/hal.h"')
        if self._key_include:
            self._emit(f'#include "{self._key_include}"')
        if self.directives.load_files:
            self._emit('#include "assets_gen.h"')
        self._emit()
        self._emit(f"#define PYXEL_WIDTH  {self.directives.width}")
        self._emit(f"#define PYXEL_HEIGHT {self.directives.height}")
        self._emit(f"#define PYXEL_FPS    {self.directives.fps}")
        self._emit()

        # Separar nodos por categoría
        classes, functions, global_stmts = [], [], []
        for stmt in node.body:
            if isinstance(stmt, ast.ClassDef):
                classes.append(stmt)
            elif isinstance(stmt, ast.FunctionDef):
                functions.append(stmt)
            elif isinstance(stmt, ast.Import):
                pass  # import pyxel — ignorar
            elif isinstance(stmt, ast.Expr):
                call = stmt.value
                if (isinstance(call, ast.Call) and
                        isinstance(call.func, ast.Attribute) and
                        isinstance(call.func.value, ast.Name) and
                        call.func.value.id == "pyxel"):
                    pass  # directiva — ignorar
                else:
                    global_stmts.append(stmt)
            else:
                global_stmts.append(stmt)

        # 1. Struct de clases
        for cls in classes:
            self._emit_class_struct(cls)

        # 2. Forward-declarations de funciones
        for fn in functions:
            sig = self._fn_signature_str(fn, is_method=False, class_name=None)
            self._emit(f"{sig};")
        if functions:
            self._emit()

        # 3. Variables globales
        for stmt in global_stmts:
            self._emit_global_stmt(stmt)
        if global_stmts:
            self._emit()

        # 4. Implementaciones de métodos de clase
        for cls in classes:
            self._emit_class_methods(cls)

        # 5. Funciones
        for fn in functions:
            self._emit_function(fn, is_method=False, class_name=None)
            self._emit()

    def _emit_global_stmt(self, stmt):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    typ = self.node_types.get(id(target), "int")
                    self._emit_var_decl("static", target.id, typ, stmt.value)
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                typ = self.node_types.get(id(stmt.target), "int")
                self._emit_var_decl("static", stmt.target.id, typ, stmt.value)

    def _emit_var_decl(self, storage: str, name: str, py_type: str,
                       init_node, array_size: Optional[str] = None):
        c_type = _py_type_to_c(py_type, self.classes)
        if py_type.startswith("list:"):
            elem_c = _py_type_to_c(py_type[5:], self.classes)
            if isinstance(init_node, ast.List):
                n = len(init_node.elts)
                elems = ", ".join(self._expr(e) for e in init_node.elts)
                self._emit(f"{storage} {elem_c} {name}[{n}] = {{{elems}}};")
            elif (isinstance(init_node, ast.BinOp) and
                  isinstance(init_node.op, ast.Mult)):
                # [x] * N
                n = self._expr(init_node.right)
                self._emit(f"{storage} {elem_c} {name}[{n}];")
            else:
                val = self._expr(init_node) if init_node else ""
                self._emit(f"{storage} {c_type} {name}{' = ' + val if val else ''};")
        else:
            val = self._expr(init_node) if init_node else ""
            if val:
                self._emit(f"{storage} {c_type} {name} = {val};")
            else:
                self._emit(f"{storage} {c_type} {name};")

    def _emit_class_struct(self, node: ast.ClassDef):
        rec = self.classes.get(node.name)
        if not rec:
            return
        self._emit(f"/* class {node.name} */")
        self._emit("typedef struct {")
        self._indent += 1
        for fname, ftype in rec.fields.items():
            self._emit(f"{_py_type_to_c(ftype, self.classes)} {fname};")
        self._indent -= 1
        self._emit(f"}} {node.name};")
        self._emit()

    def _emit_class_methods(self, node: ast.ClassDef):
        old = self._current_class
        self._current_class = node.name
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._emit_function(item, is_method=True, class_name=node.name)
                self._emit()
        self._current_class = old

    def _emit_function(self, node: ast.FunctionDef,
                       is_method: bool, class_name: Optional[str]):
        sig = self._fn_signature_str(node, is_method, class_name)
        self._emit(sig)
        self._emit("{")
        self._indent += 1

        scope_key = (f"{class_name}.{node.name}" if class_name else node.name)
        exclude = self._param_names(node)
        if is_method:
            exclude.add("self")
        self._emit_locals(scope_key, exclude)

        old_fn = self._current_fn
        self._current_fn = scope_key
        for stmt in node.body:
            self.visit(stmt)
        self._current_fn = old_fn

        self._indent -= 1
        self._emit("}")

    # ── Visitors de sentencias individuales ──────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Solo se llama si no está dentro de Module (p.ej. anidada)
        # En Module las funciones se emiten en visit_Module directamente
        pass

    def visit_ClassDef(self, node: ast.ClassDef):
        pass  # manejado en visit_Module

    def visit_Assign(self, node: ast.Assign):
        val = self._expr(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                # ¿Es un array declarado en locals como pointer (*)? → declarar inline
                locs = self._local_vars.get(self._current_fn or "", {})
                info = locs.get(target.id)
                if info and info[0].endswith("*"):
                    # array local — emitir declaración completa
                    py_type = info[1]
                    self._emit_var_decl("", target.id, py_type, node.value)
                else:
                    self._emit(f"{target.id} = {val};")
            elif isinstance(target, ast.Attribute):
                self._emit(f"{self._expr(target)} = {val};")
            elif isinstance(target, ast.Subscript):
                self._emit(f"{self._expr(target)} = {val};")

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value:
            self._emit(f"{self._expr(node.target)} = {self._expr(node.value)};")

    def visit_AugAssign(self, node: ast.AugAssign):
        ops = {
            ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=",
            ast.FloorDiv: "/=", ast.Mod: "%=",
            ast.BitAnd: "&=", ast.BitOr: "|=", ast.BitXor: "^=",
            ast.LShift: "<<=", ast.RShift: ">>=",
        }
        op_str = ops.get(type(node.op), "+=")
        self._emit(f"{self._expr(node.target)} {op_str} {self._expr(node.value)};")

    def visit_If(self, node: ast.If):
        self._emit(f"if ({self._expr(node.test)}) {{")
        self._indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self._indent -= 1

        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                n = orelse[0]
                self._emit(f"}} else if ({self._expr(n.test)}) {{")
                self._indent += 1
                for stmt in n.body:
                    self.visit(stmt)
                self._indent -= 1
                orelse = n.orelse
            else:
                self._emit("} else {")
                self._indent += 1
                for stmt in orelse:
                    self.visit(stmt)
                self._indent -= 1
                orelse = []
        self._emit("}")

    def visit_While(self, node: ast.While):
        cond = ("1" if isinstance(node.test, ast.Constant) and node.test.value is True
                else self._expr(node.test))
        self._emit(f"while ({cond}) {{")
        self._indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self._indent -= 1
        self._emit("}")

    def visit_For(self, node: ast.For):
        var = self._expr(node.target)
        args = node.iter.args  # range args
        if len(args) == 1:
            start, stop, step = "0", self._expr(args[0]), "1"
        elif len(args) == 2:
            start, stop, step = self._expr(args[0]), self._expr(args[1]), "1"
        else:
            start = self._expr(args[0])
            stop = self._expr(args[1])
            step = self._expr(args[2])

        # Si step es negativo, la condición es >
        if step.startswith("-") or step.startswith("(-"):
            cmp = ">"
        else:
            cmp = "<"
        self._emit(f"for ({var} = {start}; {var} {cmp} {stop}; {var} += {step}) {{")
        self._indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self._indent -= 1
        self._emit("}")

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            self._emit("return;")
        else:
            self._emit(f"return {self._expr(node.value)};")

    def visit_Break(self, node):
        self._emit("break;")

    def visit_Continue(self, node):
        self._emit("continue;")

    def visit_Global(self, node):
        pass  # acceso a globales es implícito en C89

    def visit_Pass(self, node):
        self._emit("/* pass */")

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call):
            c = self._call(node.value)
            if c and not c.startswith("/*") and c.strip():
                self._emit(f"{c};")


# ── API pública ───────────────────────────────────────────────────────────────

def generate(tree: ast.Module, symbols, classes: dict,
             node_types: dict, directives: CompileDirectives,
             key_include: str = "") -> str:
    gen = CodeGenerator(symbols, classes, node_types, directives, key_include)
    return gen.generate(tree)
