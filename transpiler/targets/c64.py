"""Target Commodore 64 (cc65/cl65)."""

from transpiler.targets.base import BaseTarget


class C64Target(BaseTarget):
    name = "c64"

    def hal_include_path(self) -> str:
        return "hal/c64"

    def validate_config(self, config: dict) -> list[str]:
        warnings = []
        if config.get("sync") == "halt":
            warnings.append("WARNING [c64]: sync='halt' not available on C64 — using 'raster'")
        if config.get("double_buffer") and config.get("double_buffer") is True:
            warnings.append("WARNING [c64]: double_buffer requires at least 16 KB extra RAM")
        return warnings

    def generate_main(self, update_fn: str, draw_fn: str, custom_fn: str,
                      mode: str, config: dict) -> str:
        vbl_line = config.get("vbl_line", 251)
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
            f"static void __fastcall__ vbl_handler(void)\n"
            "{\n"
            f"    {first}();\n"
            f"    {second}();\n"
            "    VIC.irr = 0x01;  /* ACK raster IRQ */\n"
            "}\n"
            "\n"
            "void main(void)\n"
            "{\n"
            "    hal_init();\n"
            f"    VIC.rasterline = {vbl_line};\n"
            "    VIC.ctrl1      |= 0x80;\n"
            "    CIA1.icr        = 0x7F;\n"
            "    irq_set_handler(vbl_handler);\n"
            "    for (;;) {}\n"
            "}"
        )

    def _build_command(self, c_files: list[str], output: str) -> str:
        files = " ".join(c_files)
        hal = "hal/c64/graphics.c hal/c64/sound.c hal/c64/input.c hal/c64/gameloop.c"
        return f"cl65 -t c64 -O -o {output} {files} {hal}"
