"""Clase abstracta que define la interfaz de cada target."""

import os
import subprocess
from abc import ABC, abstractmethod
from transpiler.frontend.validator import CompileDirectives


class BaseTarget(ABC):
    name: str = ""

    @abstractmethod
    def generate_main(self, update_fn: str, draw_fn: str, custom_fn: str,
                      mode: str, config: dict) -> str:
        """Genera el main() C específico del target."""
        ...

    @abstractmethod
    def hal_include_path(self) -> str:
        """Ruta al directorio HAL del target (relativa al proyecto)."""
        ...

    def validate_config(self, config: dict) -> list[str]:
        """Valida @pyxel.config para este target. Devuelve lista de warnings."""
        return []

    @abstractmethod
    def _build_command(self, c_files: list[str], output: str) -> str:
        """Construye el comando de toolchain."""
        ...

    def compile(self, c_files: list[str], output: str) -> tuple[bool, str]:
        """
        Invoca el toolchain.  Retorna (success, command).
        El entorno del proceso hereda PATH, por lo que basta con añadir
        el directorio bin de z88dk/cc65 al PATH del shell antes de llamar.
        """
        cmd = self._build_command(c_files, output)
        result = subprocess.run(cmd, shell=True, env=os.environ)
        return result.returncode == 0, cmd
