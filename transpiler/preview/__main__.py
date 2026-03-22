"""Entry point: python -m transpiler.preview play script.py [--target X]"""

import argparse
import sys
from pathlib import Path

from transpiler.preview.runner import run


def main():
    parser = argparse.ArgumentParser(
        prog="npyxel",
        description="npyxel player — subset validation and asset preview",
    )
    sub = parser.add_subparsers(dest="command")

    play = sub.add_parser("play", help="Validate and run a script with Pyxel")
    play.add_argument("script", help="Input Python script (.py)")
    play.add_argument(
        "--target",
        metavar="TARGET",
        default=None,
        help="Target machine for palette preview (e.g. c64, zx, cpc)",
    )

    args = parser.parse_args()

    if args.command != "play":
        parser.print_help()
        sys.exit(1)

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: file not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    run(script_path, target=args.target)


if __name__ == "__main__":
    main()
