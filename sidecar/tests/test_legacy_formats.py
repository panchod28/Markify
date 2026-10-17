import pytest

from converter import convert_document
from error_messages import get_error_message
from ocr.diagnostics import ConversionError


@pytest.mark.parametrize("name", ["informe.doc", "charla.ppt", "INFORME.DOC", "Charla.PPT"])
def test_legacy_office_files_fail_with_their_own_code_and_message(tmp_path, name):
    p = tmp_path / name
    p.write_bytes(b"\xd0\xcf\x11\xe0 binario OLE")
    with pytest.raises(ConversionError) as e:
        convert_document(str(p))
    assert (e.value.code, e.value.stage) == ("legacy_format", "open")
    assert ".docx" in get_error_message(e.value, "es") and "antiguo" in get_error_message(e.value, "es")
    assert ".pptx" in get_error_message(e.value, "en") and "Old format" in get_error_message(e.value, "en")


@pytest.mark.parametrize("name", ["datos.csv", "pagina.html"])
def test_other_formats_are_not_affected(tmp_path, name):
    p = tmp_path / name
    p.write_text("a,b\n1,2\n" if name.endswith("csv") else "<p>hola</p>", encoding="utf-8")
    assert convert_document(str(p)).strip()
