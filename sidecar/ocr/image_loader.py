# sidecar/ocr/image_loader.py
"""
Carga y normalización de imágenes para el OCR (archivo suelto, bytes de un PDF o de un DOCX/PPTX):
límite de píxeles, orientación EXIF, transparencia sobre blanco, RGB y reducción del lado mayor.
"""

import io
from pathlib import Path

from ocr.diagnostics import ConversionError

MAX_PIXELS = 100_000_000  # por encima se rechaza (imagen enorme / bomba de descompresión)
MAX_SIDE_PX = 2000        # lado mayor enviado al motor (RapidOCR reescala por encima de esto de todos modos)


def load_image(source: str | Path | bytes | io.IOBase, name: str, max_side: int = MAX_SIDE_PX):
    """Devuelve (imagen RGB, nº de fotogramas del original). `name` solo se usa en los errores (sin ruta)."""
    from PIL import Image, ImageOps  # Pillow ya viaja en el sidecar (markitdown)

    try:
        img = Image.open(io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source)  # lee solo la cabecera
        width, height = img.size
    except Image.DecompressionBombError as e:
        raise ConversionError("image_too_large", "decode", name, cause=e)
    except Exception as e:
        raise ConversionError("image_decode_failed", "decode", name, cause=e)
    if width * height > MAX_PIXELS:
        raise ConversionError("image_too_large", "decode", name)

    frames = getattr(img, "n_frames", 1)
    try:
        img = _to_rgb(ImageOps.exif_transpose(img))   # aquí se decodifica de verdad
    except Image.DecompressionBombError as e:
        raise ConversionError("image_too_large", "decode", name, cause=e)
    except Exception as e:
        raise ConversionError("image_decode_failed", "decode", name, cause=e)
    img.thumbnail((max_side, max_side), Image.LANCZOS)  # solo reduce; mantiene la proporción
    return img, frames


def _to_rgb(img):
    """RGB; la transparencia se compone sobre blanco (texto negro sobre fondo transparente sería ilegible)."""
    from PIL import Image

    if img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return img.convert("RGB")
