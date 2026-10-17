# sidecar/ocr/pdf_pipeline.py
"""
PDF -> Markdown decidiendo por página. Ver specs `pdf-page-pipeline` del change add-ocr-image-pdf-support.

- Ninguna página SCANNED (todo TEXT/BLANK/MIXED): se delega en `convert_document`, salida idéntica a la de siempre.
- Alguna página SCANNED: ruta híbrida; texto nativo con pdfminer, escaneadas con render + OCR + layout.
  (Las MIXED se tratan como TEXT hasta la Fase 3, tarea 4.1.)
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
from ocr.layout import lines_to_markdown
from ocr.page_classifier import PageKind, PageMetrics, classify_page

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
        kinds = [_classify(pdf, i) for i in range(n)]
        if PageKind.SCANNED not in kinds:
            pdf.close()
            pdf = None
            return ConversionResult(convert_document(file_path))  # ruta rápida: nada que reconocer

        if engine is None:
            from ocr.engine import get_engine  # carga perezosa del motor (OpenCV/ONNX)
            engine = get_engine()
        return _convert_pages(pdf, path, kinds, cancel_flag, on_progress, engine)
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


def _classify(pdf, i: int) -> PageKind:
    """Un fallo al medir la página no la descarta: se trata como escaneada y el render dirá si es ilegible."""
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
        areas = []
        for obj in page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]):
            left, bottom, right, top = (getattr(obj, "get_bounds", None) or obj.get_pos)()  # 5.x / 4.x
            areas.append(max(0.0, right - left) * max(0.0, top - bottom) / (width * height))
        return classify_page(PageMetrics(chars, min(1.0, sum(areas)), min(1.0, max(areas, default=0.0))))
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return PageKind.SCANNED
    finally:
        if page is not None:
            page.close()


def _convert_pages(pdf, path: Path, kinds: list[PageKind], cancel_flag, on_progress, engine) -> ConversionResult:
    from pdfminer.high_level import extract_text

    name, n = path.name, len(kinds)
    parts: list[str] = []
    warnings: list[PageIssue] = []
    first_failure: ConversionError | None = None
    dropped_total = 0

    for i, kind in enumerate(kinds):
        if cancel_flag.is_set():
            return ConversionResult("", warnings)  # main.py emite conversion_cancelled
        page_no = i + 1
        try:
            if kind == PageKind.BLANK:
                text = ""
            elif kind == PageKind.SCANNED:
                text, dropped = _ocr_page(pdf, i, engine)
                dropped_total += dropped
            else:  # TEXT y, de momento, MIXED
                # ponytail: extract_text reabre el archivo por página (O(n²) en PDFs enormes con alguna página
                # escaneada). Si molesta: un solo PDFDocument y extract_pages.
                text = extract_text(str(path), page_numbers=[i]).strip()
            if text:
                parts.append(text)
        except Exception as e:  # único punto de captura por página: una página mala no tumba el archivo
            err = e if isinstance(e, ConversionError) else ConversionError("page_failed", "assemble", cause=e)
            err.file, err.page = name, page_no
            issue = PageIssue("page_failed", err.stage, page=page_no)
            log_issue(issue, name, e)
            traceback.print_exc(file=sys.stderr)
            warnings.append(issue)
            first_failure = first_failure or err
            parts.append(f"<!-- Markify: página {page_no} no se pudo procesar ({err.code}) -->")
        on_progress(min(99, 100 * (i + 1) // n))

    if dropped_total:
        warnings.append(PageIssue("low_confidence_dropped", "layout", count=dropped_total))
    if len(parts) == sum(1 for w in warnings if w.code == "page_failed"):  # ninguna página aportó texto
        raise first_failure or ConversionError("no_text_found", "assemble", name)
    return ConversionResult("\n\n".join(parts), warnings)


def _ocr_page(pdf, i: int, engine: OcrEngine) -> tuple[str, int]:
    """Render de una sola página + OCR + layout. Devuelve (texto, líneas descartadas por baja confianza)."""
    try:
        page = pdf[i]
        try:
            width, height = page.get_size()
            scale = min(RENDER_DPI / 72, MAX_SIDE_PX / max(width, height))
            image = page.render(scale=scale).to_pil().convert("RGB")
        finally:
            page.close()
    except Exception as e:
        raise ConversionError("page_render_failed", "render", cause=e)
    return lines_to_markdown(engine.recognize(image))
