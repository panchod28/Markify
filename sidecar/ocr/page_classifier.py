# sidecar/ocr/page_classifier.py
"""
Clasificación de páginas de PDF a partir de métricas ya medidas. Función pura: sin pdfium, sin OCR.
Umbrales calibrados en el spike del change add-ocr-image-pdf-support (S6).
"""

from dataclasses import dataclass
from enum import Enum

MIN_TEXT_CHARS = 25     # caracteres no blancos: una capa de texto con al menos esto manda (no se hace OCR)
IMAGE_MIN_AREA = 0.05   # una imagen por debajo de esta fracción de la página es decoración (logo, viñeta)
SCAN_COVERAGE = 0.5     # imágenes que cubren al menos esto de la página = página escaneada / fondo completo


class PageKind(Enum):
    TEXT = "text"
    SCANNED = "scanned"
    MIXED = "mixed"
    BLANK = "blank"


@dataclass(frozen=True)
class PageMetrics:
    text_chars: int        # caracteres no blancos de la capa de texto
    coverage: float        # fracción de la página cubierta por imágenes (suma, tope 1.0)
    largest_image: float   # fracción de la página que ocupa la imagen más grande


def classify_page(m: PageMetrics) -> PageKind:
    has_text = m.text_chars >= MIN_TEXT_CHARS
    if has_text:
        # Imagen relevante pero no fondo de página: texto nativo + figura con posible texto.
        # Si la imagen cubre la página (escaneo con capa de texto previa), la capa de texto manda.
        if IMAGE_MIN_AREA <= m.largest_image and m.coverage < SCAN_COVERAGE:
            return PageKind.MIXED
        return PageKind.TEXT
    if m.coverage >= SCAN_COVERAGE or m.largest_image >= IMAGE_MIN_AREA:
        return PageKind.SCANNED
    if m.text_chars == 0:
        return PageKind.BLANK
    return PageKind.TEXT  # poco texto y sin imágenes relevantes: una portada corta, un número de página
