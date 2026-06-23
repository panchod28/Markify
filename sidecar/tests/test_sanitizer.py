import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sanitizer import sanitize_filename


@pytest.mark.parametrize("original,expected", [
    ("Mi Presentación 2024.pptx",    "mi_presentacion_2024.md"),
    ("Reporte Anual (Final).pdf",    "reporte_anual_final.md"),
    ("audio grabación #3.mp3",       "audio_grabacion_3.md"),
    ("!@#$%.xlsx",                   "archivo_sin_nombre.md"),
    ("MAYÚSCULAS.pdf",               "mayusculas.md"),
    ("file.with.dots.pdf",           "file_with_dots.md"),
    ("123.pdf",                      "123.md"),
    ("   espacios   .pdf",           "espacios.md"),
    ("___guiones___.pdf",            "guiones.md"),
])
def test_sanitize_filename(original, expected):
    assert sanitize_filename(original) == expected
