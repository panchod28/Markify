# sidecar/ocr/recognize.py
"""
Lectura de una imagen con el motor OCR + layout. Compartida por imágenes sueltas, PDFs y documentos de Office.
Ambas funciones devuelven (texto Markdown, líneas descartadas por baja confianza).
"""

from ocr.base import OcrEngine
from ocr.diagnostics import ConversionError
from ocr.layout import MIN_CONFIDENCE, lines_to_markdown


def read_simple(image, engine: OcrEngine) -> tuple[str, int]:
    """Un único OCR a 0°. Una imagen sin texto devuelve ("", n): no es un error."""
    return lines_to_markdown(engine.recognize(image))


def read_upright(image, engine: OcrEngine) -> tuple[str, int]:
    """OCR a 0°; si no se lee texto, prueba 90/180/270° y conserva la orientación con mayor suma
    confianza × longitud. Solo cuentan las líneas horizontales: el motor también lee texto vertical (página
    girada 90°) con confianza alta, pero con cajas que el layout no sabe ordenar.
    Lanza ConversionError("ocr_failed") si ninguna orientación lee texto."""
    best, best_score = ("", 0), 0.0
    for angle in (0, 90, 180, 270):
        lines = [l for l in engine.recognize(image.rotate(angle, expand=True) if angle else image)
                 if l.box[2] - l.box[0] >= l.box[3] - l.box[1]]
        candidate = lines_to_markdown(lines)
        score = sum(l.confidence * len(l.text) for l in lines if l.confidence >= MIN_CONFIDENCE)
        if candidate[0] and score > best_score:
            best, best_score = candidate, score
        if angle == 0 and best[0]:
            return best  # página recta: sin reintentos
    if not best[0]:
        raise ConversionError("ocr_failed", "ocr")
    return best
