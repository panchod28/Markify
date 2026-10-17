# sidecar/ocr/image_converter.py
"""
Imagen -> Markdown con OCR local. Ver specs `image-conversion` del change add-ocr-image-pdf-support.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ocr.base import OcrEngine
from ocr.diagnostics import ConversionError, PageIssue
from ocr.layout import lines_to_markdown

MAX_PIXELS = 100_000_000  # por encima se rechaza (imagen enorme / bomba de descompresión)
MAX_SIDE_PX = 2000        # lado mayor enviado al motor (RapidOCR reescala por encima de esto de todos modos)


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

    from PIL import Image, ImageOps  # Pillow ya viaja en el sidecar (markitdown)

    try:
        img = Image.open(path)          # lee solo la cabecera
        width, height = img.size
    except Image.DecompressionBombError as e:
        raise ConversionError("image_too_large", "decode", name, cause=e)
    except Exception as e:
        raise ConversionError("image_decode_failed", "decode", name, cause=e)
    if width * height > MAX_PIXELS:
        raise ConversionError("image_too_large", "decode", name)

    frames = getattr(img, "n_frames", 1)
    try:
        img = ImageOps.exif_transpose(img).convert("RGB")   # aquí se decodifica de verdad
    except Image.DecompressionBombError as e:
        raise ConversionError("image_too_large", "decode", name, cause=e)
    except Exception as e:
        raise ConversionError("image_decode_failed", "decode", name, cause=e)
    img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX), Image.LANCZOS)  # solo reduce; mantiene la proporción

    if engine is None:
        from ocr.engine import get_engine  # carga perezosa del motor
        engine = get_engine()

    text, dropped = lines_to_markdown(engine.recognize(img))

    warnings: list[PageIssue] = []
    if dropped:
        warnings.append(PageIssue("low_confidence_dropped", "layout", count=dropped))
    if frames > 1:
        warnings.append(PageIssue("frames_skipped", "decode", count=frames - 1))

    if not text.strip():
        raise ConversionError("no_text_found", "ocr", name)
    return ConversionResult(text, warnings)
