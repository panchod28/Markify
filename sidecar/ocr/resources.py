# sidecar/ocr/resources.py
"""
Ruta de los recursos empaquetados (modelos OCR). No usar model_manager.get_model_path(): esa es una
carpeta de datos descargables; los modelos OCR viajan dentro del binario y nunca se descargan en runtime.
"""

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    # Empaquetado (PyInstaller): sys._MEIPASS apunta a _internal/. Desarrollo: la carpeta sidecar/.
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)
