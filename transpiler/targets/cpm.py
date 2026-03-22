"""Target CP/M (Z80, z88dk)."""

from transpiler.targets.base import BaseTarget


class CPMTarget(BaseTarget):
    name = "cpm"

    def hal_include_path(self) -> str:
        return "hal/cpm"

    def validate_config(self, config: dict) -> list[str]:
        warnings = []
        if config.get("sync") in ("vbl", "raster"):
            warnings.append("WARNING [cpm]: sync='vbl'/'raster' not available — using 'cycles'")
        if "vbl_line" in config:
            warnings.append("WARNING [cpm]: vbl_line has no effect on CP/M")
        if "irq_priority" in config:
            warnings.append("WARNING [cpm]: irq_priority has no effect on CP/M")
        if "irq_stack" in config:
            warnings.append("WARNING [cpm]: irq_stack has no effect on CP/M")
        if config.get("double_buffer"):
            warnings.append("WARNING [cpm]: double_buffer not supported on CP/M")
        return warnings

    def generate_main(self, update_fn: str, draw_fn: str, custom_fn: str,
                      mode: str, config: dict) -> str:
        fps = config.get("fps", 50)
        cycles_per_frame = 4_000_000 // fps   # ~4 MHz Z80 / fps
        update_first = config.get("update_first", True)

        lines = ["void main(void)", "{", "    hal_init();"]

        if mode == "CUSTOM":
            lines.append(f"    {custom_fn}();")
        else:
            first, second = (update_fn, draw_fn) if update_first else (draw_fn, update_fn)
            lines += [
                "    for (;;) {",
                f"        {first}();",
                f"        {second}();",
                f"        hal_wait_cycles({cycles_per_frame}U);",
                "    }",
            ]

        lines.append("}")
        return "\n".join(lines)

    def _build_command(self, c_files: list[str], output: str) -> str:
        files = " ".join(c_files)
        hal = "hal/cpm/graphics.c hal/cpm/sound.c hal/cpm/input.c hal/cpm/gameloop.c"
        return f"zcc +cpm -O2 -o {output} {files} {hal}"
