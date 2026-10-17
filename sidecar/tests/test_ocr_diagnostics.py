import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from error_messages import get_error_message, issue_to_payload
from ocr.diagnostics import ConversionError, PageIssue, log_issue


def test_conversion_error_carries_context_and_cause():
    cause = OSError("disco")
    err = ConversionError("ocr_failed", "ocr", "/Users/ana/docs/informe.pdf", page=4, cause=cause)
    assert (err.code, err.stage, err.file, err.page) == ("ocr_failed", "ocr", "informe.pdf", 4)
    assert err.__cause__ is cause
    assert "page=4" in str(err) and "informe.pdf" in str(err)
    assert "/Users/ana" not in str(err)  # solo el nombre, sin rutas completas


def test_log_issue_is_one_stderr_line_without_full_path(capsys):
    log_issue(PageIssue("ocr_failed", "ocr", page=7), "/Users/ana/docs/informe.pdf", RuntimeError("boom"))
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("[Sidecar][ocr] file=informe.pdf page=7 stage=ocr code=ocr_failed")
    assert "RuntimeError: boom" in lines[0] and "/Users/ana" not in lines[0]


def test_error_message_by_code_in_both_languages():
    err = ConversionError("image_too_large", "decode", "x.png")
    assert get_error_message(err, "es") == "La imagen es demasiado grande para procesarla"
    assert get_error_message(err, "en") == "The image is too large to process"
    assert get_error_message(ConversionError("no_text_found", "ocr"), "es") == "No se encontró texto en el archivo"


def test_all_ocr_codes_have_es_and_en_messages():
    for code in ["no_text_found", "image_decode_failed", "image_too_large", "ocr_engine_unavailable", "ocr_failed"]:
        e = ConversionError(code, "ocr")
        assert get_error_message(e, "es") != get_error_message(e, "en") or code == "x"
        assert get_error_message(e, "es") != "Error inesperado al convertir el archivo"


def test_legacy_mapping_is_unchanged():
    assert get_error_message(PermissionError("x"), "es") == "El archivo está protegido con contraseña"
    assert get_error_message(FileNotFoundError("x"), "en") == "Could not find the file"
    assert get_error_message(ValueError("vacío"), "es") == "No se encontró texto en el archivo"
    assert get_error_message(RuntimeError("file_corrupted"), "en").startswith("Could not read the file")
    assert get_error_message(Exception("raro"), "es") == "Error inesperado al convertir el archivo"


def test_issue_to_payload():
    p = issue_to_payload(PageIssue("low_confidence_dropped", "layout", count=6), "es")
    assert p == {"page": None, "stage": "layout", "code": "low_confidence_dropped",
                 "message": "Se omitieron 6 líneas con baja confianza de lectura"}
    assert issue_to_payload(PageIssue("page_failed", "render", page=7), "en")["message"] == "Page 7 could not be processed"
    assert issue_to_payload(PageIssue("desconocido", "x"), "en")["message"] == "desconocido"
