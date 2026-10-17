# sidecar/ocr/pdf_pipeline.py
"""
PDF -> Markdown decidiendo por página. Ver specs `pdf-page-pipeline` del change add-ocr-image-pdf-support.

- Todo TEXT/BLANK: se delega en `convert_document`, salida idéntica a la de siempre.
- Alguna página SCANNED o MIXED: ruta híbrida. TEXT = texto nativo con pdfminer; SCANNED = render + OCR + layout
  (con reintento de orientación); MIXED = texto nativo + OCR de cada imagen relevante, después del texto.
"""

import sys
import threading
import traceback
from pathlib import Path
from typing import Callable

from converter import convert_document
from ocr.base import OcrEngine
from ocr.diagnostics import ConversionError, PageIssue, log_issue
from ocr.image_converter import ConversionResult
from ocr.recognize import read_simple, read_upright
from ocr.page_classifier import IMAGE_MIN_AREA, PageKind, PageMetrics, classify_page

Box = tuple[float, float, float, float]  # (izq, abajo, der, arriba) en puntos, en el espacio sin rotar de la página

RENDER_DPI = 150
MAX_SIDE_PX = 1800  # lado mayor del bitmap enviado al motor (design D5)


def convert_pdf(
    file_path: str,
    cancel_flag: threading.Event,
    on_progress: Callable[[int], None],
    engine: OcrEngine | None = None,
) -> ConversionResult:
    path = Path(file_path)
    name = path.name

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    if path.stat().st_size == 0:
        raise ValueError("El archivo está vacío")

    import pypdfium2 as pdfium  # perezoso: solo hace falta con PDFs

    pdf = _open(pdfium, file_path, name)
    try:
        n = len(pdf)
        if n == 0:
            raise ConversionError("pdf_open_failed", "open", name)
        pages = [_measure(pdf, i) for i in range(n)]
        if not any(kind in (PageKind.SCANNED, PageKind.MIXED) for kind, _ in pages):
            pdf.close()
            pdf = None
            return ConversionResult(convert_document(file_path))  # ruta rápida: nada que reconocer

        if engine is None:
            from ocr.engine import get_engine  # carga perezosa del motor (OpenCV/ONNX)
            engine = get_engine()
        return _convert_pages(pdf, path, pages, cancel_flag, on_progress, engine)
    finally:
        if pdf is not None:
            pdf.close()


def _open(pdfium, file_path: str, name: str):
    try:
        return pdfium.PdfDocument(file_path)
    except pdfium.PdfiumError as e:
        if "password" in str(e).lower():
            raise PermissionError("Archivo protegido con contraseña")
        raise ConversionError("pdf_open_failed", "open", name, cause=e)


def _measure(pdf, i: int) -> tuple[PageKind, list[Box]]:
    """Clase de la página y cajas de sus imágenes relevantes. Un fallo al medir no descarta la página: se trata
    como escaneada y el render dirá si es ilegible."""
    import pypdfium2.raw as pdfium_c

    page = None
    try:
        page = pdf[i]
        width, height = page.get_size()
        textpage = page.get_textpage()
        try:
            chars = len("".join(textpage.get_text_range().split()))
        finally:
            textpage.close()
        boxes, areas = [], []
        for obj in page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]):
            box = (getattr(obj, "get_bounds", None) or obj.get_pos)()  # 5.x / 4.x
            area = max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1]) / (width * height)
            areas.append(area)
            if area >= IMAGE_MIN_AREA:
                boxes.append(box)
        kind = classify_page(PageMetrics(chars, min(1.0, sum(areas)), min(1.0, max(areas, default=0.0))))
        return kind, boxes
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return PageKind.SCANNED, []
    finally:
        if page is not None:
            page.close()


def _convert_pages(pdf, path: Path, pages, cancel_flag, on_progress, engine) -> ConversionResult:
    from pdfminer.high_level import extract_text

    name, n = path.name, len(pages)
    parts: list[str] = []
    warnings: list[PageIssue] = []
    first_failure: ConversionError | None = None
    dropped_total = 0
    produced_text = False

    for i, (kind, boxes) in enumerate(pages):
        if cancel_flag.is_set():
            return ConversionResult("", warnings)  # main.py emite conversion_cancelled
        page_no = i + 1
        page_parts: list[str] = []  # lo ya extraído de esta página sobrevive a un fallo posterior (p. ej. OCR de una figura)
        try:
            if kind in (PageKind.TEXT, PageKind.MIXED):
                # ponytail: extract_text reabre el archivo por página (O(n²) en PDFs enormes con alguna página
                # escaneada). Si molesta: un solo PDFDocument y extract_pages.
                native = extract_text(str(path), page_numbers=[i]).strip()
                if native:
                    page_parts.append(native)
                    produced_text = True
            if kind in (PageKind.SCANNED, PageKind.MIXED):
                texts, dropped = _ocr_page(pdf, i, engine, boxes if kind == PageKind.MIXED else None)
                dropped_total += dropped
                for text in texts:
                    page_parts.append(text)
                    produced_text = True
        except Exception as e:  # único punto de captura por página: una página mala no tumba el archivo
            err = e if isinstance(e, ConversionError) else ConversionError("page_failed", "assemble", cause=e)
            err.file, err.page = name, page_no
            issue = PageIssue("page_failed", err.stage, page=page_no)
            log_issue(issue, name, e)
            traceback.print_exc(file=sys.stderr)
            warnings.append(issue)
            first_failure = first_failure or err
            page_parts.append(f"<!-- Markify: página {page_no} no se pudo procesar ({err.code}) -->")
        parts.extend(page_parts)
        on_progress(min(99, 100 * (i + 1) // n))

    if dropped_total:
        warnings.append(PageIssue("low_confidence_dropped", "layout", count=dropped_total))
    if not produced_text:
        raise first_failure or ConversionError("no_text_found", "assemble", name)
    return ConversionResult("\n\n".join(parts), warnings)


def _ocr_page(pdf, i: int, engine: OcrEngine, boxes: list[Box] | None) -> tuple[list[str], int]:
    """Render de una sola página y OCR: de la página entera (`boxes` None) o de cada imagen relevante.
    Devuelve (textos no vacíos, líneas descartadas por baja confianza)."""
    try:
        page = pdf[i]
        try:
            width, height = page.get_size()  # tamaño en pantalla, ya con /Rotate
            scale = min(RENDER_DPI / 72, MAX_SIDE_PX / max(width, height))
            rotation = page.get_rotation()
            image = page.render(scale=scale).to_pil().convert("RGB")
        finally:
            page.close()
    except Exception as e:
        raise ConversionError("page_render_failed", "render", cause=e)

    if boxes is None:
        results = [read_upright(image, engine)]
    else:
        results = []
        for box in boxes:
            crop = image.crop(_to_pixels(box, width, height, rotation, scale))
            results.append(read_simple(crop, engine))
    return [text for text, _ in results if text], sum(dropped for _, dropped in results)


def _to_pixels(box: Box, width: float, height: float, rotation: int, scale: float) -> tuple[int, int, int, int]:
    """Caja de pdfium (espacio sin rotar, origen abajo-izquierda) -> píxeles del bitmap renderizado.
    `width`/`height` son el tamaño en pantalla; ponytail: asume MediaBox con origen en (0, 0)."""
    unrotated_w, unrotated_h = (width, height) if rotation in (0, 180) else (height, width)

    def to_screen(x: float, y: float) -> tuple[float, float]:
        if rotation == 90:
            return y, unrotated_w - x
        if rotation == 180:
            return unrotated_w - x, unrotated_h - y
        if rotation == 270:
            return unrotated_h - y, x
        return x, y

    (x0, y0), (x1, y1) = to_screen(box[0], box[1]), to_screen(box[2], box[3])
    pad = 2  # píxeles de margen para no cortar el borde de las letras
    left, right = sorted((x0 * scale, x1 * scale))
    top, bottom = sorted(((height - y0) * scale, (height - y1) * scale))
    return (max(0, int(left) - pad), max(0, int(top) - pad), int(right) + pad, int(bottom) + pad)
