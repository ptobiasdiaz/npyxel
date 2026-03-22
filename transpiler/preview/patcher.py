"""
Monkey-patch de pyxel.load() para interceptar y convertir assets.
En v0.0.1 (sin --target) es un no-op: los assets se cargan tal cual.
"""


def patch_load(target=None):
    """Instala el patch de pyxel.load() para el target dado.
    Con target=None no hace nada — Pyxel carga los assets en su paleta original.
    """
    if target is None:
        return
    # Implementación futura: convertir paleta según target
    raise NotImplementedError(f"Target preview not yet implemented: {target}")
