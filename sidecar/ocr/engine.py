# sidecar/ocr/engine.py
"""
Frontera de los motores OCR. Los consumidores (image_converter, pdf_pipeline) dependen solo de OcrEngine.
Añadir un motor nuevo = un archivo con una clase que implemente `recognize` + una línea en ENGINES.
"""

import os
import threading
from typing import Callable

from ocr.base import OcrEngine, OcrLine  # noqa: F401  (re-export)
from ocr.rapidocr_engine import RapidOcrEngine


ENGINES: dict[str, Callable[[], OcrEngine]] = {"rapidocr": RapidOcrEngine}
DEFAULT_ENGINE = "rapidocr"

_instances: dict[str, OcrEngine] = {}
_lock = threading.Lock()


def get_engine(name: str | None = None) -> OcrEngine:
    """Instancia única y perezosa por motor (los modelos se cargan la primera vez que se pide)."""
    name = name or os.environ.get("MARKIFY_OCR_ENGINE", DEFAULT_ENGINE)
    with _lock:
        if name not in _instances:
            _instances[name] = ENGINES[name]()
        return _instances[name]
