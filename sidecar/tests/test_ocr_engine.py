import socket
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr import resources
from ocr.diagnostics import ConversionError
from ocr.rapidocr_engine import RapidOcrEngine


def test_resource_path_in_dev_points_to_sidecar_folder():
    assert resources.resource_path("ocr", "models") == Path(__file__).resolve().parent.parent / "ocr" / "models"


def test_resource_path_when_frozen_uses_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert resources.resource_path("ocr", "models") == tmp_path / "ocr" / "models"


def test_missing_models_raise_engine_unavailable_naming_the_resource(tmp_path):
    with pytest.raises(ConversionError) as e:
        RapidOcrEngine(models_dir=tmp_path)
    assert (e.value.code, e.value.stage) == ("ocr_engine_unavailable", "ocr")
    assert "ch_PP-OCRv5_det_mobile.onnx" in str(e.value) and "latin_PP-OCRv5_rec_mobile.onnx" in str(e.value)


def _models_available():
    d = resources.resource_path("ocr", "models")
    return (d / "ch_PP-OCRv5_det_mobile.onnx").exists() and (d / "latin_PP-OCRv5_rec_mobile.onnx").exists()


@pytest.mark.ocr
def test_real_engine_reads_text_offline(monkeypatch, tmp_path):
    pytest.importorskip("rapidocr")
    if not _models_available():
        pytest.skip("faltan los modelos: python fetch_ocr_models.py")

    # Sin red: cualquier intento de conexión (p. ej. descargar modelos) debe fallar el test.
    def deny(*a, **k):
        raise OSError("NETWORK BLOCKED")
    monkeypatch.setattr(socket.socket, "connect", deny)

    from ocr.image_converter import convert_image
    from ocr.engine import get_engine

    img = Image.new("RGB", (1200, 300), "white")
    font = ImageFont.load_default(size=48)
    ImageDraw.Draw(img).text((40, 40), "Hello world 2024", font=font, fill="black")
    ImageDraw.Draw(img).text((40, 140), "Markify converts documents", font=font, fill="black")
    p = tmp_path / "t.png"
    img.save(p)

    result = convert_image(str(p), get_engine())
    text = result.markdown.lower()
    assert "hello world" in text and "2024" in text
    assert "markify converts documents" in text
