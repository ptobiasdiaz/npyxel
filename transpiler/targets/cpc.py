"""Target Amstrad CPC 464 (z88dk/zcc +cpc)."""

from transpiler.targets.base import BaseTarget


class CPCTarget(BaseTarget):
    name = "cpc"

    def hal_include_path(self) -> str:
        return "hal/cpc"

    def validate_config(self, config: dict) -> list[str]:
        warnings = []
        if config.get("vbl_line") is not None:
            warnings.append("WARNING [cpc]: vbl_line has no effect on CPC")
        if config.get("double_buffer"):
            warnings.append("WARNING [cpc]: double_buffer not implemented for CPC")
        if config.get("sync") == "raster":
            warnings.append("WARNING [cpc]: sync='raster' not available — using 'halt'")
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
            '        __asm__("HALT");   /* sync 50 Hz PAL via Gate Array VSYNC interrupt */\n'
            "        hal_flip();        /* update frame counter + keyboard state */\n"
            f"        {first}();\n"
            f"        {second}();\n"
            "    }\n"
            "}"
        )

    def _build_command(self, c_files: list[str], output: str) -> str:
        files = " ".join(c_files)
        hal = (
            "hal/cpc/graphics.c hal/cpc/sound.c "
            "hal/cpc/input.c hal/cpc/gameloop.c "
            "hal/common/bresenham.c hal/common/strconv.c"
        )
        ext = output.rsplit(".", 1)[-1].lower() if "." in output else "dsk"
        base = output[:-(len(ext) + 1)]

        if ext == "cdt":
            # -create-app hace que zcc genere {base}.cpc (binario AMSDOS)
            # 2cdt convierte ese .cpc a un CDT con cabecera ZXTape!\x1A válida.
            name = base.rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:16].upper()
            return (
                f"zcc +cpc -O2 -I. -create-app -o {base}.bin {files} {hal} && "
                f"2cdt -n -r {name} {base}.cpc {output}"
            )
        # default: .dsk via iDSK
        return (
            f"zcc +cpc -O2 -I. -o {base}.bin {files} {hal} && "
            f"iDSK {output} -n && "
            f"iDSK {output} -i {base}.bin -t 1"
        )
