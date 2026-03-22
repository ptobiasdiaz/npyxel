"""
Mapa pyxel.* -> función HAL en C89 y tipos de parámetros esperados.

Valor None significa "directiva de compilación": no genera código C.
"""

# HAL_SIGNATURES: attr -> (nombre_C, [tipos_param])
HAL_SIGNATURES: dict[str, tuple | None] = {
    # ── Gráficos: primitivas ──────────────────────────────────────────────
    "cls":    ("hal_cls",    ["int"]),
    "pset":   ("hal_pset",   ["int", "int", "int"]),
    "pget":   ("hal_pget",   ["int", "int"]),
    "line":   ("hal_line",   ["int", "int", "int", "int", "int"]),
    "rect":   ("hal_rect",   ["int", "int", "int", "int", "int"]),
    "rectb":  ("hal_rectb",  ["int", "int", "int", "int", "int"]),
    "circ":   ("hal_circ",   ["int", "int", "int", "int"]),
    "circb":  ("hal_circb",  ["int", "int", "int", "int"]),
    "elli":   ("hal_elli",   ["int", "int", "int", "int", "int"]),
    "ellib":  ("hal_ellib",  ["int", "int", "int", "int", "int"]),
    "tri":    ("hal_tri",    ["int", "int", "int", "int", "int", "int", "int"]),
    "trib":   ("hal_trib",   ["int", "int", "int", "int", "int", "int", "int"]),
    "fill":   ("hal_fill",   ["int", "int", "int"]),
    # ── Gráficos: blitter ─────────────────────────────────────────────────
    "blt":    ("hal_blt",    ["int", "int", "int", "int", "int", "int", "int", "int"]),
    "bltm":   ("hal_bltm",   ["int", "int", "int", "int", "int", "int", "int", "int"]),
    # ── Texto ─────────────────────────────────────────────────────────────
    "text":   ("hal_text",   ["int", "int", "str", "int"]),
    # ── Input ─────────────────────────────────────────────────────────────
    "btn":    ("hal_btn",    ["int"]),
    "btnp":   ("hal_btnp",   ["int", "int", "int"]),
    "btnr":   ("hal_btnr",   ["int"]),
    # ── Sonido ────────────────────────────────────────────────────────────
    "play":       ("hal_play",     ["int", "int", "int"]),
    "playm":      ("hal_playm",    ["int", "int"]),
    "stop":       ("hal_stop",     ["int"]),
    "play_pos":   ("hal_play_pos", ["int"]),
    # ── Sistema ───────────────────────────────────────────────────────────
    "quit":   ("hal_quit",   []),
    "flip":   ("hal_flip",   []),
    "show":   ("hal_flip",   []),  # show = flip de un frame
    # ── Directivas (sin código C generado) ───────────────────────────────
    "init":       None,
    "load":       None,
    "run":        None,
    "run_custom": None,
}

# Constantes de teclado/gamepad: pyxel.KEY_* -> constante HAL
KEY_CONSTANTS: dict[str, str] = {
    **{f"KEY_{c}": f"HAL_KEY_{c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    **{f"KEY_{d}": f"HAL_KEY_{d}" for d in "0123456789"},
    "KEY_UP":        "HAL_KEY_UP",
    "KEY_DOWN":      "HAL_KEY_DOWN",
    "KEY_LEFT":      "HAL_KEY_LEFT",
    "KEY_RIGHT":     "HAL_KEY_RIGHT",
    "KEY_SPACE":     "HAL_KEY_SPACE",
    "KEY_RETURN":    "HAL_KEY_RETURN",
    "KEY_ESCAPE":    "HAL_KEY_ESCAPE",
    "KEY_BACKSPACE": "HAL_KEY_BACKSPACE",
    "KEY_TAB":       "HAL_KEY_TAB",
    "GAMEPAD1_BUTTON_A":     "HAL_GP1_A",
    "GAMEPAD1_BUTTON_B":     "HAL_GP1_B",
    "GAMEPAD1_BUTTON_UP":    "HAL_GP1_UP",
    "GAMEPAD1_BUTTON_DOWN":  "HAL_GP1_DOWN",
    "GAMEPAD1_BUTTON_LEFT":  "HAL_GP1_LEFT",
    "GAMEPAD1_BUTTON_RIGHT": "HAL_GP1_RIGHT",
}
