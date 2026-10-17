import re
import threading

import pytest

from converter import convert_document
from make_office_fixtures import make_pptx_corpus  # noqa: F401  (fixture en conftest)
from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.office_images import convert_pptx


class FakeEngine:
    name = "fake"

    def __init__(self, text="texto reconocido de la imagen", fail_on=(), on_call=None, empty=False, upside=False):
        self.calls, self.text, self.fail_on, self.on_call, self.empty, self.upside = 0, text, set(fail_on), on_call, empty, upside

    def recognize(self, image):
        self.calls += 1
        if self.on_call:
            self.on_call(self.calls)
        if self.calls in self.fail_on:
            raise ConversionError("ocr_failed", "ocr", cause=RuntimeError("boom"))
        if self.empty or (self.upside and self.calls < 3):
            return []
        return [OcrLine(f"{self.text} {self.calls}", (5, 5, 300, 40), 0.99)]


def run(path, engine=None, cancel=None, progress=None):
    return convert_pptx(str(path), cancel or threading.Event(), (progress.append if progress is not None else lambda p: None), engine)


def without_image_lines(md):
    return "\n".join(l for l in md.split("\n") if not re.match(r"^!\[[^\]]*\]\([^)]*\)$", l))


squash = lambda t: re.sub(r"\n{2,}", "\n", t).strip()


# --- ruta rápida y no regresión ----------------------------------------------------------------

def test_pptx_without_images_is_identical_to_convert_document_and_skips_ocr(pptx_files):
    engine = FakeEngine()
    assert run(pptx_files["solo_texto"], engine).markdown == convert_document(str(pptx_files["solo_texto"]))
    assert engine.calls == 0


def test_only_image_lines_differ_from_markitdown(pptx_files):
    ours = run(pptx_files["tabla_y_notas"], FakeEngine(empty=True)).markdown
    theirs = without_image_lines(convert_document(str(pptx_files["tabla_y_notas"])))
    assert squash(ours) == squash(theirs)
    assert "| Enero | 1200 |" in ours and "### Notes:" in ours and "Notas del orador" in ours


def test_a_pptx_that_is_not_a_zip_gets_exactly_the_same_result_as_before(tmp_path):
    bad = tmp_path / "roto.pptx"
    bad.write_bytes(b"esto no es un zip")
    try:
        expected = convert_document(str(bad))
    except Exception as e:
        with pytest.raises(type(e)):
            run(bad, FakeEngine())
    else:
        assert run(bad, FakeEngine()).markdown == expected


def test_missing_and_empty_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path / "no.pptx")
    empty = tmp_path / "vacio.pptx"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="vacío"):
        run(empty)


# --- OCR con motor falso ------------------------------------------------------------------------

def test_text_takes_the_picture_position_with_real_alt(pptx_files):
    result = run(pptx_files["con_figura"], FakeEngine())
    md = result.markdown
    order = ["Texto antes de la figura", "*Captura del sistema*", "texto reconocido de la imagen 1", "Texto después de la figura"]
    assert [md.index(t) for t in order] == sorted(md.index(t) for t in order), md
    assert "![" not in md and ".jpg" not in md and result.warnings == []


def test_icons_are_not_read_but_a_real_alt_text_is_kept(pptx_files):
    engine = FakeEngine()
    md = run(pptx_files["iconos"], engine).markdown
    assert engine.calls == 0 and "*Correo de contacto*" in md and "![" not in md


def test_filename_alt_text_is_dropped(pptx_files):
    md = run(pptx_files["repetida"], FakeEngine()).markdown
    assert "image.png" not in md


def test_picture_inside_a_group_and_in_a_placeholder_are_read(pptx_files):
    assert "texto reconocido" in run(pptx_files["en_grupo"], FakeEngine()).markdown
    assert "texto reconocido" in run(pptx_files["marcador"], FakeEngine()).markdown


def test_repeated_picture_is_read_once_and_only_first_slide_gets_the_text(pptx_files):
    engine = FakeEngine()
    md = run(pptx_files["repetida"], engine).markdown
    assert engine.calls == 1 and md.count("texto reconocido de la imagen") == 1
    assert md.index("texto reconocido") < md.index("<!-- Slide number: 2 -->")


@pytest.mark.parametrize("text", ["Q", "xy 1", "—"])
def test_text_with_fewer_than_six_alphanumerics_is_discarded(pptx_files, text):
    class Exact(FakeEngine):
        def recognize(self, image):
            return [OcrLine(text, (5, 5, 300, 40), 0.99)]
    assert run(pptx_files["con_figura"], Exact()).markdown == run(pptx_files["con_figura"], FakeEngine(empty=True)).markdown


def test_full_slide_picture_uses_the_orientation_retry(pptx_files):
    engine = FakeEngine(upside=True)
    md = run(pptx_files["pagina_completa_180"], engine).markdown
    assert "texto reconocido" in md and engine.calls == 4  # 0°, 90°, 180° y 270°


def test_small_figure_without_text_costs_one_inference_and_no_warning(pptx_files):
    engine = FakeEngine(empty=True)
    result = run(pptx_files["con_figura"], engine)
    assert engine.calls == 1 and result.warnings == [] and "![" not in result.markdown


def test_corrupt_image_warns_with_the_slide_number_and_keeps_the_rest(pptx_files):
    result = run(pptx_files["imagen_corrupta"], FakeEngine())
    assert "Rota" in result.markdown
    assert [(w.code, w.page) for w in result.warnings] == [("image_failed", 1)]


def test_unsupported_image_type_is_counted_in_one_warning(pptx_files):
    engine = FakeEngine()
    result = run(pptx_files["tipo_emf"], engine)
    assert engine.calls == 0 and [(w.code, w.count) for w in result.warnings] == [("images_skipped", 1)]


def test_an_image_that_explodes_becomes_a_warning_for_its_slide(pptx_files):
    result = run(pptx_files["tres_distintas"], FakeEngine(fail_on={2}))
    assert result.markdown.count("texto reconocido") == 2
    assert [(w.code, w.stage, w.page) for w in result.warnings] == [("image_failed", "ocr", 2)]


def test_progress_and_cancel_between_images(pptx_files):
    progress = []
    run(pptx_files["tres_distintas"], FakeEngine(), progress=progress)
    assert progress == [33, 66, 99]
    cancel = threading.Event()
    engine = FakeEngine(on_call=lambda n: cancel.set() if n == 1 else None)
    assert run(pptx_files["tres_distintas"], engine, cancel).markdown == "" and engine.calls == 1


def test_missing_engine_is_a_file_error(pptx_files, monkeypatch):
    import ocr.engine
    def boom(name=None):
        raise ConversionError("ocr_engine_unavailable", "ocr")
    monkeypatch.setattr(ocr.engine, "get_engine", boom)
    with pytest.raises(ConversionError) as e:
        run(pptx_files["con_figura"])
    assert e.value.code == "ocr_engine_unavailable"


# --- OCR real -----------------------------------------------------------------------------------

def _models_available():
    from ocr.resources import resource_path
    return (resource_path("ocr", "models") / "latin_PP-OCRv5_rec_mobile.onnx").exists()


@pytest.mark.ocr
@pytest.mark.skipif(not _models_available(), reason="faltan los modelos OCR (fetch_ocr_models.py)")
class TestRealOcr:
    def test_screenshot_with_accents_between_texts(self, pptx_files):
        md = run(pptx_files["con_figura"]).markdown
        assert "conversión" in md and "niños" in md and md.index("antes") < md.index("conversión") < md.index("después")

    def test_scanned_slide_rotated_180(self, pptx_files):
        md = run(pptx_files["pagina_completa_180"]).markdown
        assert "conversión" in md and "pingüinos" in md

    def test_diagram_in_a_group(self, pptx_files):
        assert "Diagrama de flujo" in run(pptx_files["en_grupo"]).markdown
