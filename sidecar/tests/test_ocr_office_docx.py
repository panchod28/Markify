import re
import threading
from pathlib import Path

import pytest

from converter import convert_document
from make_fixtures import ES_LINES
from make_office_fixtures import build_docx, img, png_bytes, text_page
from ocr import office_images
from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.office_images import alnum_count, convert_docx, image_paragraphs, real_alt


class FakeEngine:
    name = "fake"

    def __init__(self, text="texto reconocido de la imagen", fail_on=(), on_call=None, empty=False):
        self.calls, self.text, self.fail_on, self.on_call, self.empty = 0, text, set(fail_on), on_call, empty

    def recognize(self, image):
        self.calls += 1
        if self.on_call:
            self.on_call(self.calls)
        if self.calls in self.fail_on:
            raise ConversionError("ocr_failed", "ocr", cause=RuntimeError("boom"))
        return [] if self.empty else [OcrLine(f"{self.text} {self.calls}", (5, 5, 300, 40), 0.99)]


def run(path, engine=None, cancel=None, progress=None):
    return convert_docx(str(path), cancel or threading.Event(), (progress.append if progress is not None else lambda p: None), engine)


# --- utilidades puras --------------------------------------------------------------------------

@pytest.mark.parametrize("alt, name, expected", [
    ("Captura del sistema", None, "Captura del sistema"),
    ("image.png", None, ""), ("foto.JPG", "x", ""), ("Imagen 3", None, ""), ("Picture 12", None, ""), ("Gráfico 4", None, ""),
    ("Rectángulo 5", "Rectángulo 5", ""), ("", None, ""), (None, None, ""),
    ("  Diagrama   de flujo ", None, "Diagrama de flujo"), ("con *asteriscos*", None, "con asteriscos"),
])
def test_real_alt(alt, name, expected):
    assert real_alt(alt, name) == expected


def test_alnum_count_and_paragraphs():
    assert alnum_count("D") == 1 and alnum_count("Total 42") == 7 and alnum_count("- · —") == 0
    assert image_paragraphs("Alt", "uno\n\ndos") == ["*Alt*", "uno", "dos"]
    assert image_paragraphs("", "uno") == ["uno"] and image_paragraphs("", "") == []


# --- ruta rápida y no regresión ----------------------------------------------------------------

def test_docx_without_images_is_identical_to_convert_document_and_skips_ocr(docx_files):
    engine = FakeEngine()
    assert run(docx_files["solo_texto"], engine).markdown == convert_document(str(docx_files["solo_texto"]))
    assert engine.calls == 0


def test_only_image_lines_differ_from_markitdown(docx_files):
    ours = run(docx_files["foto_sin_texto"], FakeEngine(empty=True)).markdown
    theirs = "\n".join(l for l in convert_document(str(docx_files["foto_sin_texto"])).split("\n") if not l.startswith("!["))
    squash = lambda t: re.sub(r"\n{2,}", "\n\n", t).strip()
    assert squash(ours) == squash(theirs) == "Una foto:"


def test_pre_process_docx_is_still_used(docx_files, monkeypatch):
    import markitdown.converter_utils.docx.pre_process as pre
    calls = []
    original = pre.pre_process_docx
    monkeypatch.setattr(pre, "pre_process_docx", lambda f: calls.append(1) or original(f))
    run(docx_files["captura_entre_parrafos"], FakeEngine())
    assert calls == [1]


def test_a_docx_that_is_not_a_zip_gets_exactly_the_same_result_as_before(tmp_path):
    bad = tmp_path / "roto.docx"
    bad.write_bytes(b"esto no es un zip")
    assert run(bad, FakeEngine()).markdown == convert_document(str(bad))


def test_missing_and_empty_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path / "no.docx")
    empty = tmp_path / "vacio.docx"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="vacío"):
        run(empty)


# --- OCR con motor falso ------------------------------------------------------------------------

def test_text_replaces_the_image_in_place_with_real_alt(docx_files):
    result = run(docx_files["captura_entre_parrafos"], FakeEngine())
    md = result.markdown
    order = ["Antes de la imagen.", "*Captura del sistema*", "texto reconocido de la imagen 1", "Después de la imagen."]
    assert [md.index(t) for t in order] == sorted(md.index(t) for t in order), md
    assert "![" not in md and "data:" not in md and result.warnings == []


def test_document_with_only_an_image_and_progress(docx_files):
    progress = []
    result = run(docx_files["solo_imagen"], FakeEngine(), progress=progress)
    assert result.markdown == "texto reconocido de la imagen 1" and progress == [99]


def test_image_inside_a_table_cell_stays_on_one_line(docx_files):
    md = run(docx_files["imagen_en_tabla"], FakeEngine("texto en celda\n\ncon dos párrafos")).markdown
    row = [l for l in md.split("\n") if "Celda A" in l][0]
    assert row.startswith("| Celda A | ") and "texto en celda" in row and "con dos párrafos" not in md.replace(row, "") and "![" not in md


def test_photo_without_text_leaves_no_trace_and_no_warning(docx_files):
    result = run(docx_files["foto_sin_texto"], FakeEngine(empty=True))
    assert "![" not in result.markdown and result.warnings == []


def test_icons_are_not_sent_to_the_engine_but_the_logo_is(docx_files):
    engine = FakeEngine()
    run(docx_files["iconos_y_logo"], engine)
    assert engine.calls == 1  # iconos de 32 px (0.1 % de la página) fuera; logotipo de 240 × 70 px dentro


def test_repeated_image_is_read_once_and_its_text_appears_once(docx_files):
    engine = FakeEngine()
    md = run(docx_files["misma_imagen_repetida"], engine).markdown
    assert engine.calls == 1 and md.count("texto reconocido de la imagen") == 1


def test_automatic_alt_text_is_dropped(docx_files):
    md = run(docx_files["alt_automatico"], FakeEngine()).markdown
    assert "image.png" not in md and "Imagen 3" not in md


@pytest.mark.parametrize("text", ["Q", "xy 1", "—"])
def test_text_with_fewer_than_six_alphanumerics_is_discarded(docx_files, text):
    class Exact(FakeEngine):
        def recognize(self, image):
            return [OcrLine(text, (5, 5, 300, 40), 0.99)]
    nothing = run(docx_files["captura_entre_parrafos"], FakeEngine(empty=True)).markdown
    assert run(docx_files["captura_entre_parrafos"], Exact()).markdown == nothing


def test_unsupported_image_types_are_counted_in_one_warning(docx_files):
    engine = FakeEngine()
    result = run(docx_files["emf_y_captura"], engine)
    assert engine.calls == 1 and [(w.code, w.count) for w in result.warnings] == [("images_skipped", 2)]


def test_corrupt_image_keeps_the_rest_and_warns(docx_files):
    result = run(docx_files["imagen_corrupta"], FakeEngine())
    assert "Hola" in result.markdown and "Fin" in result.markdown
    assert [(w.code, w.page) for w in result.warnings] == [("image_failed", None)]


def test_an_image_that_explodes_becomes_a_warning_and_the_next_one_is_read(tmp_path):
    shots = [png_bytes(text_page(ES_LINES, size=40 + i, px=(900, 420))) for i in range(3)]
    path = build_docx(tmp_path / "tres.docx", [img(s, 600, 280) for s in shots])
    result = run(path, FakeEngine(fail_on={2}))
    assert result.markdown.count("texto reconocido") == 2
    assert [(w.code, w.stage) for w in result.warnings] == [("image_failed", "ocr")]


def test_progress_and_cancel_between_images(tmp_path):
    shots = [png_bytes(text_page(ES_LINES, size=40 + i, px=(900, 420))) for i in range(4)]
    path = build_docx(tmp_path / "cuatro.docx", [img(s, 600, 280) for s in shots])
    progress = []
    run(path, FakeEngine(), progress=progress)
    assert progress == [25, 50, 75, 99]
    cancel = threading.Event()
    engine = FakeEngine(on_call=lambda n: cancel.set() if n == 2 else None)
    assert run(path, engine, cancel).markdown == "" and engine.calls == 2


def test_missing_engine_is_a_file_error_not_an_image_warning(docx_files, monkeypatch):
    import ocr.engine
    def boom(name=None):
        raise ConversionError("ocr_engine_unavailable", "ocr")
    monkeypatch.setattr(ocr.engine, "get_engine", boom)
    with pytest.raises(ConversionError) as e:
        run(docx_files["solo_imagen"])
    assert e.value.code == "ocr_engine_unavailable"


def test_pixel_fallback_when_the_displayed_size_is_unknown(docx_files, monkeypatch):
    monkeypatch.setattr(office_images, "_docx_geometry", lambda zf: ({}, 8.5 * 11, 0))
    engine = FakeEngine()
    run(docx_files["iconos_y_logo"], engine)   # 32 px y 240 × 70 px: ninguno llega a 100 px de lado menor
    assert engine.calls == 0
    run(docx_files["captura_entre_parrafos"], engine)  # 900 × 420 px sí
    assert engine.calls == 1


def test_page_sized_images_use_the_orientation_retry(docx_files):
    class Upside(FakeEngine):
        def recognize(self, image):
            self.calls += 1
            return [] if self.calls < 3 else [OcrLine("texto de la página girada", (5, 5, 300, 40), 0.99)]
    engine = Upside()
    assert "texto de la página girada" in run(docx_files["pagina_escaneada_180"], engine).markdown and engine.calls == 4  # 0°, 90°, 180° y 270°


def test_small_figure_without_text_costs_one_inference(docx_files):
    engine = FakeEngine(empty=True)
    run(docx_files["captura_entre_parrafos"], engine)
    assert engine.calls == 1


# --- OCR real -----------------------------------------------------------------------------------

def _models_available():
    from ocr.resources import resource_path
    return (resource_path("ocr", "models") / "latin_PP-OCRv5_rec_mobile.onnx").exists()


@pytest.mark.ocr
@pytest.mark.skipif(not _models_available(), reason="faltan los modelos OCR (fetch_ocr_models.py)")
class TestRealOcr:
    def test_screenshot_between_paragraphs(self, docx_files):
        md = run(docx_files["captura_entre_parrafos"]).markdown
        assert "conversión" in md and "niños" in md and md.index("Antes") < md.index("conversión") < md.index("Después")

    def test_diagram_in_a_table_cell(self, docx_files):
        row = [l for l in run(docx_files["imagen_en_tabla"]).markdown.split("\n") if "Celda A" in l][0]
        assert "Diagrama de flujo" in row

    def test_scanned_page_rotated_180(self, docx_files):
        md = run(docx_files["pagina_escaneada_180"]).markdown
        assert "conversión" in md and "pingüinos" in md

    def test_photo_without_text_adds_nothing(self, docx_files):
        assert run(docx_files["foto_sin_texto"]).markdown.strip() == "Una foto:"
