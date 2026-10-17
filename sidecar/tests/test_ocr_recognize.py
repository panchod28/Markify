import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.recognize import read_simple, read_upright

IMG = Image.new("RGB", (200, 100), "white")


def line(text="hola mundo", box=(10, 10, 300, 40), conf=0.99):
    return OcrLine(text, box, conf)


class Engine:
    """Devuelve lo que diga `script[n]` para la n-ésima llamada (lista vacía si no hay más)."""
    name = "script"

    def __init__(self, script):
        self.script, self.sizes = script, []

    def recognize(self, image):
        self.sizes.append(image.size)
        n = len(self.sizes) - 1
        return self.script[n] if n < len(self.script) else []


def test_read_simple_is_a_single_inference_and_no_text_is_not_an_error():
    engine = Engine([[]])
    assert read_simple(IMG, engine) == ("", 0)
    assert len(engine.sizes) == 1


def test_read_simple_reports_low_confidence_lines_dropped():
    text, dropped = read_simple(IMG, Engine([[line("bueno"), line("ruido", conf=0.1)]]))
    assert (text, dropped) == ("bueno", 1)


def test_read_upright_straight_page_does_not_retry():
    engine = Engine([[line()]])
    assert read_upright(IMG, engine)[0] == "hola mundo" and len(engine.sizes) == 1


def test_read_upright_retries_and_keeps_the_best_orientation():
    # 0°: nada; 90°: algo flojo; 180°: bueno; 270°: nada
    engine = Engine([[], [line("flojo", conf=0.55)], [line("excelente texto", conf=0.99)], []])
    assert read_upright(IMG, engine)[0] == "excelente texto" and len(engine.sizes) == 4


def test_read_upright_ignores_vertical_lines_as_text():
    vertical = line("vertical", box=(10, 10, 40, 400))
    engine = Engine([[vertical], [line("recto")]])
    assert read_upright(IMG, engine)[0] == "recto"


def test_read_upright_rotates_the_image_for_the_retries():
    engine = Engine([[], [line()]])
    wide = Image.new("RGB", (300, 100))
    read_upright(wide, engine)
    assert engine.sizes[:2] == [(300, 100), (100, 300)]  # 90° intercambia ancho y alto


def test_read_upright_without_text_in_any_orientation_is_an_ocr_failure():
    with pytest.raises(ConversionError) as e:
        read_upright(IMG, Engine([]))
    assert (e.value.code, e.value.stage) == ("ocr_failed", "ocr")
