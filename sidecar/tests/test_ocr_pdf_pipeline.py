import threading
from difflib import SequenceMatcher

import pytest

from converter import convert_document
from make_fixtures import ES_LINES, EN_LINES, scan_pdf
from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.pdf_pipeline import convert_pdf


class FakeEngine:
    name = "fake"

    def __init__(self, fail_on=(), error=None, on_call=None):
        self.calls = 0
        self.fail_on = set(fail_on)
        self.error = error or (lambda: ConversionError("ocr_failed", "ocr"))  # una instancia nueva por fallo
        self.on_call = on_call

    def recognize(self, image):
        self.calls += 1
        if self.on_call:
            self.on_call(self.calls)
        if self.calls in self.fail_on:
            raise self.error()
        return [OcrLine(f"OCR pagina {self.calls}", (10, 10, 400, 40), 0.99)]


def run(path, engine=None, cancel=None, progress=None):
    return convert_pdf(str(path), cancel or threading.Event(), (progress.append if progress is not None else lambda p: None), engine)


@pytest.fixture
def scan4(tmp_path):
    p = tmp_path / "scan4.pdf"
    scan_pdf(p, [ES_LINES, EN_LINES, ES_LINES, EN_LINES])
    return p


# --- ruta rápida: sin regresión -------------------------------------------------------------

@pytest.mark.parametrize("name", ["text", "text_multi", "text_table", "scan_text_layer"])
def test_text_pdfs_are_identical_to_convert_document_and_skip_ocr(pdfs, name):
    engine = FakeEngine()
    assert run(pdfs[name], engine).markdown == convert_document(str(pdfs[name]))
    assert engine.calls == 0


def test_blank_pdf_keeps_the_existing_no_text_error(pdfs):
    with pytest.raises(ValueError, match="No se encontró texto"):
        run(pdfs["blank"], FakeEngine())


# --- ruta híbrida con motor falso -----------------------------------------------------------

def test_mixed_classes_are_assembled_in_page_order(pdfs):
    engine, progress = FakeEngine(), []
    result = run(pdfs["scan_mixed"], engine, progress=progress)
    md = result.markdown
    assert md.index("Intro") < md.index("OCR pagina 1") < md.index("Fin")  # texto, escaneada, (blanca), texto
    assert engine.calls == 1
    assert "\n\n\n" not in md and result.warnings == []
    assert progress == [25, 50, 75, 99]  # 4 páginas; la última se topa en 99, el 100 lo envía main.py


def test_progress_is_percent_of_processed_pages(scan4):
    progress = []
    run(scan4, FakeEngine(), progress=progress)
    assert progress == [25, 50, 75, 99]


def test_a_page_that_explodes_becomes_a_marker_and_a_warning(scan4):
    engine = FakeEngine(fail_on={2}, error=lambda: RuntimeError("boom"))
    result = run(scan4, engine)
    assert "OCR pagina 1" in result.markdown and "OCR pagina 4" in result.markdown
    assert "<!-- Markify: página 2 no se pudo procesar (page_failed) -->" in result.markdown
    assert [(w.code, w.page) for w in result.warnings] == [("page_failed", 2)]


def test_unreadable_page_keeps_the_rest_and_names_render_stage(pdfs):
    result = run(pdfs["bad_page"], FakeEngine())
    assert "<!-- Markify: página 2 no se pudo procesar (page_render_failed) -->" in result.markdown
    assert "OCR pagina 1" in result.markdown and "OCR pagina 2" in result.markdown
    assert [(w.code, w.stage, w.page) for w in result.warnings] == [("page_failed", "render", 2)]


def test_all_pages_failing_raises_the_first_cause_code(scan4):
    engine = FakeEngine(fail_on={1, 2, 3, 4})
    with pytest.raises(ConversionError) as e:
        run(scan4, engine)
    assert (e.value.code, e.value.page, e.value.file) == ("ocr_failed", 1, "scan4.pdf")


def test_scanned_page_with_no_readable_text_in_any_orientation_is_an_ocr_failure(scan4):
    engine = FakeEngine(fail_on=set())
    engine.recognize = lambda image: []  # ni a 0° ni girada
    with pytest.raises(ConversionError) as e:
        run(scan4, engine)
    assert (e.value.code, e.value.page) == ("ocr_failed", 1)


def test_no_native_text_and_no_figure_text_without_failures_raises_no_text_found(pdfs, monkeypatch):
    import pdfminer.high_level
    monkeypatch.setattr(pdfminer.high_level, "extract_text", lambda *a, **k: "  ")
    engine = FakeEngine()
    engine.recognize = lambda image: []  # la figura no tiene texto (en MIXED no hay reintento de orientación)
    with pytest.raises(ConversionError) as e:
        run(pdfs["mixed_diagram"], engine)
    assert e.value.code == "no_text_found"


def test_low_confidence_lines_are_reported_once_for_the_file(scan4):
    class Shaky(FakeEngine):
        def recognize(self, image):
            return [OcrLine("bueno", (0, 0, 100, 30), 0.9), OcrLine("ruido", (0, 50, 100, 80), 0.1)]

    result = run(scan4, Shaky())
    assert [(w.code, w.count, w.page) for w in result.warnings] == [("low_confidence_dropped", 4, None)]


def test_cancel_mid_document_stops_before_the_next_page(scan4):
    cancel = threading.Event()
    engine = FakeEngine(on_call=lambda n: cancel.set() if n == 2 else None)
    result = run(scan4, engine, cancel)
    assert result.markdown == ""
    assert engine.calls == 2  # la página 2 terminó; la 3 no empezó


def test_cancel_before_start_does_no_ocr(scan4):
    cancel = threading.Event()
    cancel.set()
    engine = FakeEngine()
    assert run(scan4, engine, cancel).markdown == ""
    assert engine.calls == 0


# --- errores fatales ------------------------------------------------------------------------

def test_encrypted_pdf_raises_the_existing_permission_error(pdfs):
    with pytest.raises(PermissionError, match="protegido con contraseña"):
        run(pdfs["encrypted"], FakeEngine())


def test_truncated_pdf_is_pdf_open_failed(pdfs):
    with pytest.raises(ConversionError) as e:
        run(pdfs["truncated"], FakeEngine())
    assert (e.value.code, e.value.stage) == ("pdf_open_failed", "open")


def test_pdf_with_zero_pages_is_pdf_open_failed(tmp_path):
    p = tmp_path / "zero.pdf"
    p.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
                  b"trailer<</Root 1 0 R/Size 3>>\n%%EOF\n")
    with pytest.raises(ConversionError) as e:
        run(p, FakeEngine())
    assert e.value.code == "pdf_open_failed"


def test_missing_and_empty_files_keep_their_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path / "nope.pdf")
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="vacío"):
        run(empty)


# --- OCR real -------------------------------------------------------------------------------

def _models_available():
    from ocr.resources import resource_path
    return (resource_path("ocr", "models") / "latin_PP-OCRv5_rec_mobile.onnx").exists()


def cer(expected: str, got: str) -> float:
    norm = lambda s: " ".join(s.split())
    return 1 - SequenceMatcher(None, norm(expected), norm(got)).ratio()  # aproximado y optimista, como en el spike


@pytest.mark.ocr
@pytest.mark.skipif(not _models_available(), reason="faltan los modelos OCR (fetch_ocr_models.py)")
@pytest.mark.parametrize("name, lines", [("scan_es", ES_LINES), ("scan_en", EN_LINES)])
def test_real_ocr_reads_a_scanned_pdf(pdfs, name, lines):
    md = run(pdfs[name]).markdown
    assert cer(" ".join(lines), md) <= 0.05, md
    if name == "scan_es":
        assert "conversión" in md and "niños" in md and "¿" in md and "¡" in md, md


# --- páginas MIXED --------------------------------------------------------------------------

class RecordingEngine(FakeEngine):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.sizes = []

    def recognize(self, image):
        self.sizes.append(image.size)
        return super().recognize(image)


def test_mixed_page_appends_ocr_of_the_figure_after_the_native_text(pdfs):
    engine = RecordingEngine()
    md = run(pdfs["mixed_diagram"], engine).markdown
    assert md.index("Texto: línea 12") < md.index("OCR pagina 1")
    assert md.count("Texto: línea 1 ") == 1 and md.count("OCR pagina") == 1
    # recorte de la figura (450×200 pt a 150 DPI ≈ 937×417 px), no la página entera (1240×1754)
    (w, h), = engine.sizes
    assert abs(w - 937) < 10 and abs(h - 417) < 10


def test_crop_follows_the_page_rotation(pdfs):
    engine = RecordingEngine()
    run(pdfs["mixed_diagram_rot90"], engine)
    (w, h), = engine.sizes
    assert abs(w - 417) < 10 and abs(h - 937) < 10  # girada 90°: el recorte es vertical


def test_decoration_only_page_is_text_and_gets_no_ocr(pdfs):
    engine = FakeEngine()
    assert run(pdfs["mixed_logo"], engine).markdown == convert_document(str(pdfs["mixed_logo"]))
    assert engine.calls == 0


def test_mixed_figure_failure_keeps_the_native_text(pdfs):
    result = run(pdfs["mixed_diagram"], FakeEngine(fail_on={1}))
    assert "Texto: línea 12" in result.markdown
    assert "<!-- Markify: página 1 no se pudo procesar (ocr_failed) -->" in result.markdown
    assert [(w.code, w.page) for w in result.warnings] == [("page_failed", 1)]


# --- orientación ----------------------------------------------------------------------------

def _text_line(n):
    return [OcrLine(f"texto {n}", (10, 10, 400, 40), 0.99)]


def test_rotation_retry_picks_the_orientation_that_reads(scan4):
    seen = []

    class Turned(FakeEngine):
        def recognize(self, image):
            seen.append(image.size)
            self.calls += 1
            return _text_line(self.calls) if self.calls % 4 == 3 else []  # solo a 180° (3.ª llamada de cada página)

    result = run(scan4, Turned())
    assert result.warnings == [] and result.markdown.startswith("texto 3")
    assert len(seen) == 16  # 4 páginas × (0°, 90°, 180°, 270°)


def test_straight_page_does_not_retry(scan4):
    engine = FakeEngine()
    run(scan4, engine)
    assert engine.calls == 4


def test_vertical_lines_do_not_count_as_text_at_0_degrees(tmp_path):
    p = tmp_path / "one.pdf"
    scan_pdf(p, [ES_LINES])

    class Sideways(FakeEngine):
        def recognize(self, image):
            self.calls += 1
            if self.calls == 1:
                return [OcrLine("vertical", (10, 10, 40, 400), 0.99)]  # texto de una página girada, leído de lado
            return _text_line(self.calls) if self.calls == 2 else []

    engine = Sideways()
    assert run(p, engine).markdown == "texto 2" and engine.calls == 4


@pytest.mark.ocr
@pytest.mark.skipif(not _models_available(), reason="faltan los modelos OCR (fetch_ocr_models.py)")
class TestRealRotationAndLayout:
    EXPECTED = " ".join(ES_LINES)

    def _count(self):
        from ocr.engine import get_engine
        real = get_engine()

        class Count:
            name = "count"
            calls = 0

            def recognize(self, image):
                self.calls += 1
                return real.recognize(image)

        return Count()

    @pytest.mark.parametrize("angle", [90, 180, 270])
    def test_scans_rotated_by_any_quarter_turn_are_read(self, tmp_path, angle):
        from make_fixtures import scan_pdf_images, text_page
        p = tmp_path / "r.pdf"
        scan_pdf_images(p, [text_page(ES_LINES).rotate(angle, expand=True)])
        result = run(p)
        assert cer(self.EXPECTED, result.markdown) <= 0.05, result.markdown
        assert result.warnings == []

    def test_rotate_attribute_is_respected_without_retries(self, pdfs):
        engine = self._count()
        md = run(pdfs["scan_rotate_attr"], engine).markdown
        assert cer(self.EXPECTED, md) <= 0.05, md
        assert engine.calls == 1

    def test_mixed_page_reads_the_diagram_once(self, pdfs):
        md = run(pdfs["mixed_diagram"]).markdown
        assert md.count("Diagrama de flujo") == 1 and "Entrada" in md and "Fase uno" in md
        assert md.index("Texto: línea 12") < md.index("Diagrama de flujo")

    def test_two_columns_read_column_by_column_with_the_footer_last(self, pdfs):
        md = run(pdfs["scan_two_columns"]).markdown
        order = ["Primera columna", "termina aqui", "Segunda columna", "cierra el documento", "Pagina 1"]
        assert [md.index(t) for t in order] == sorted(md.index(t) for t in order), md
