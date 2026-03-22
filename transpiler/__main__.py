"""Entry point: python -m transpiler script.py --target <t> --output <o>"""

import argparse
import sys
from pathlib import Path

from transpiler.frontend.validator import validate, TranspilerError
from transpiler.frontend.type_inference import infer_types
from transpiler.backend.codegen import generate
from transpiler.targets.cpm import CPMTarget
from transpiler.targets.c64 import C64Target
from transpiler.targets.zx_spectrum import ZXTarget
from transpiler.targets.cpc import CPCTarget

TARGETS = {
    "cpm": CPMTarget,
    "c64": C64Target,
    "zx":  ZXTarget,
    "cpc": CPCTarget,
}


def main():
    parser = argparse.ArgumentParser(
        description="pyxel-retro transpiler — Python/Pyxel → 8-bit native binary"
    )
    parser.add_argument("script", help="Input Python script (.py)")
    parser.add_argument("--target", required=True, choices=TARGETS,
                        help="Target architecture")
    parser.add_argument("--output", required=True,
                        help="Output file (.prg / .tap / .com)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print generated C to stdout, skip toolchain")
    parser.add_argument("-c", "--c-only", action="store_true",
                        help="Write .c file and print toolchain command, but do not invoke it")
    parser.add_argument("--show-commands", action="store_true",
                        help="Print build commands that would be executed, without running anything")
    args = parser.parse_args()

    src_path = Path(args.script)
    if not src_path.exists():
        print(f"ERROR: file not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    source = src_path.read_text(encoding="utf-8")

    # ── Stage 1: validate ────────────────────────────────────────────────
    try:
        tree, directives = validate(source)
    except TranspilerError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    # ── Stage 2: type inference ──────────────────────────────────────────
    try:
        symbols, classes, node_types = infer_types(tree, directives)
    except TranspilerError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    # ── Stage 3: code generation ─────────────────────────────────────────
    target = TARGETS[args.target]()

    if directives.config:
        for w in target.validate_config(directives.config):
            print(w, file=sys.stderr)

    key_include = f"{target.hal_include_path()}/input_keys.h"
    c_body = generate(tree, symbols, classes, node_types, directives, key_include)

    # El game loop / main() lo genera el target
    c_main = target.generate_main(
        update_fn=directives.update_fn or "update",
        draw_fn=directives.draw_fn or "draw",
        custom_fn=directives.custom_fn or "loop",
        mode=directives.game_loop_mode,
        config={**_default_config(args.target), **directives.config},
    )

    full_c = c_body + "\n\n" + c_main + "\n"

    # ── Output ───────────────────────────────────────────────────────────
    out_path = Path(args.output)

    if args.show_commands:
        c_file = out_path.with_suffix(".c")
        cmd = target._build_command([str(c_file)], args.output)
        print(cmd)
        return

    if args.dry_run:
        print(full_c)
        return

    c_file = out_path.with_suffix(".c")
    c_file.write_text(full_c, encoding="utf-8")
    print(f"Generated C: {c_file}")

    if args.c_only:
        cmd = target._build_command([str(c_file)], args.output)
        print(f"Toolchain:   {cmd}")
        return

    ok, cmd = target.compile([str(c_file)], args.output)
    print(f"Toolchain:   {cmd}")
    if not ok:
        print("ERROR: toolchain failed — check PATH and z88dk/cc65 installation",
              file=sys.stderr)
        sys.exit(1)
    print(f"Output:      {args.output}")


def _default_config(target_name: str) -> dict:
    defaults = {
        "c64": {"sync": "raster", "vbl_line": 251, "fps": 50,
                "irq_priority": "high", "irq_stack": 256,
                "double_buffer": False, "update_first": True},
        "zx":  {"sync": "halt", "fps": 50,
                "irq_priority": "normal", "irq_stack": 128,
                "double_buffer": False, "update_first": True},
        "cpm": {"sync": "cycles", "fps": 50,
                "double_buffer": False, "update_first": True},
        "cpc": {"sync": "halt", "fps": 50,
                "irq_priority": "normal", "irq_stack": 128,
                "double_buffer": False, "update_first": True},
    }
    return defaults.get(target_name, {})


if __name__ == "__main__":
    main()
