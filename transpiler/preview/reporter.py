"""Formato de mensajes de error y warning en consola."""

import sys


def ok(msg: str):
    print(f"\u2713 {msg}")


def fail(msg: str):
    print(f"\u2717 {msg}", file=sys.stderr)


def warn(msg: str):
    print(f"\u26a0 {msg}")


def launch(msg: str):
    print(f"\u25b6 {msg}")


def show_errors(title: str, errors: str):
    fail(title)
    for line in errors.splitlines():
        print(f"  {line}", file=sys.stderr)
