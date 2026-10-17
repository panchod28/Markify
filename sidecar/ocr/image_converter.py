# sidecar/ocr/image_converter.py
"""
Imagen -> Markdown con OCR local. Ver specs `image-conversion` del change add-ocr-image-pdf-support.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ocr.base import OcrEngine
from ocr.diagnostics import ConversionError, PageIssue
from ocr.image_loader import load_image
from ocr.recognize import read_simple


@dataclass
class ConversionResult:
    markdown: str
    warnings: list[PageIssue] = field(default_factory=list)


def convert_image(file_path: str, engine: OcrEngine | None = None) -> ConversionResult:
    path = Path(file_path)
    name = path.name

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    if path.stat().st_size == 0:
        raise ValueError("El archivo está vacío")

    img, frames = load_image(path, name)

    if engine is None:
        from ocr.engine import get_engine  # carga perezosa del motor
        engine = get_engine()

    text, dropped = read_simple(img, engine)

    warnings: list[PageIssue] = []
    if dropped:
        warnings.append(PageIssue("low_confidence_dropped", "layout", count=dropped))
    if frames > 1:
        warnings.append(PageIssue("frames_skipped", "decode", count=frames - 1))

    if not text.strip():
        raise ConversionError("no_text_found", "ocr", name)
    return ConversionResult(text, warnings)
