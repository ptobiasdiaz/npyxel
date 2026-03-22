"""Target ZX Spectrum (z88dk/zcc)."""

from transpiler.targets.base import BaseTarget


class ZXTarget(BaseTarget):
    name = "zx"

    def hal_include_path(self) -> str:
        return "hal/zx"

    def validate_config(self, config: dict) -> list[str]:
        warnings = []
        if config.get("vbl_line") is not None:
            warnings.append("WARNING [zx]: vbl_line has no effect on ZX Spectrum")
        if config.get("double_buffer"):
            warnings.append("WARNING [zx]: double_buffer not supported on ZX Spectrum")
        if config.get("sync") == "raster":
            warnings.append("WARNING [zx]: sync='raster' not available — using 'halt'")
        return warnings

    def generate_main(self, update_fn: str, draw_fn: str, custom_fn: str,
                      mode: str, config: dict) -> str:
        update_first = config.get("update_first", True)

        if mode == "CUSTOM":
            return (
                "void main(void)\n"
                "{\n"
                "    hal_init();\n"
                f"    {custom_fn}();\n"
                "}"
            )

        first, second = (update_fn, draw_fn) if update_first else (draw_fn, update_fn)
        return (
            "void main(void)\n"
            "{\n"
            "    hal_init();\n"
            "    for (;;) {\n"
            '        __asm__("HALT");   /* sync 50 Hz PAL via ULA interrupt */\n'
            "        hal_flip();        /* update frame counter + keyboard state */\n"
            f"        {first}();\n"
            f"        {second}();\n"
            "    }\n"
            "}"
        )

    def _build_command(self, c_files: list[str], output: str) -> str:
        files = " ".join(c_files)
        hal = (
            "hal/zx/graphics.c hal/zx/sound.c "
            "hal/zx/input.c hal/zx/gameloop.c "
            "hal/common/bresenham.c hal/common/strconv.c"
        )
        ext = output.rsplit(".", 1)[-1].lower() if "." in output else "tap"
        base = output[:-(len(ext) + 1)]
        return (
            f"zcc +zx -O2 -I. -o {base}.bin {files} {hal} && "
            f"z88dk-appmake +zx --binfile {base}.bin --org 32768 -o {output}"
        )
