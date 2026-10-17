import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr import image_converter
from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.image_converter import convert_image


class FakeEngine:
    name = "fake"

    def __init__(self, lines=None):
        self.lines = lines if lines is not None else [OcrLine("Hola mundo", (10, 10, 200, 40), 0.99)]
        self.seen = []

    def recognize(self, image):
        self.seen.append(image)
        return self.lines


def png(tmp_path, size=(200, 100), name="a.png", **save_kw):
    p = tmp_path / name
    Image.new("RGB", size, "white").save(p, **save_kw)
    return str(p)


def test_converts_with_the_given_engine(tmp_path):
    result = convert_image(png(tmp_path), FakeEngine())
    assert result.markdown == "Hola mundo"
    assert result.warnings == []


def test_no_text_raises_no_text_found(tmp_path):
    with pytest.raises(ConversionError) as e:
        convert_image(png(tmp_path), FakeEngine(lines=[]))
    assert (e.value.code, e.value.stage, e.value.file) == ("no_text_found", "ocr", "a.png")


def test_low_confidence_lines_become_an_aggregated_warning(tmp_path):
    lines = [OcrLine("bueno", (0, 0, 50, 20), 0.9)] + [OcrLine("ruido", (0, 30 * i, 50, 30 * i + 20), 0.2) for i in range(1, 4)]
    result = convert_image(png(tmp_path), FakeEngine(lines))
    assert result.markdown == "bueno"
    assert [(w.code, w.count) for w in result.warnings] == [("low_confidence_dropped", 3)]


def test_missing_and_empty_files_keep_the_existing_exceptions(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_image(str(tmp_path / "no.png"), FakeEngine())
    empty = tmp_path / "e.png"
    empty.write_bytes(b"")
    with pytest.raises(ValueError):
        convert_image(str(empty), FakeEngine())


def test_corrupt_image_is_image_decode_failed(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"esto no es un png" * 10)
    with pytest.raises(ConversionError) as e:
        convert_image(str(bad), FakeEngine())
    assert (e.value.code, e.value.stage) == ("image_decode_failed", "decode")


def test_truncated_image_is_image_decode_failed(tmp_path):
    good = Path(png(tmp_path, size=(400, 400), name="g.png"))
    (tmp_path / "t.png").write_bytes(good.read_bytes()[:60])
    with pytest.raises(ConversionError) as e:
        convert_image(str(tmp_path / "t.png"), FakeEngine())
    assert e.value.code == "image_decode_failed"


def test_too_many_pixels_is_image_too_large_without_running_ocr(tmp_path, monkeypatch):
    monkeypatch.setattr(image_converter, "MAX_PIXELS", 1000)
    engine = FakeEngine()
    with pytest.raises(ConversionError) as e:
        convert_image(png(tmp_path, size=(200, 100)), engine)
    assert e.value.code == "image_too_large" and engine.seen == []


def test_large_images_are_downscaled_for_the_engine(tmp_path):
    engine = FakeEngine()
    convert_image(png(tmp_path, size=(5000, 2500)), engine)
    w, h = engine.seen[0].size
    assert max(w, h) == image_converter.MAX_SIDE_PX and abs(w / h - 2.0) < 0.01


def test_small_images_are_not_upscaled(tmp_path):
    engine = FakeEngine()
    convert_image(png(tmp_path, size=(300, 100)), engine)
    assert engine.seen[0].size == (300, 100)


def test_exif_orientation_is_applied(tmp_path):
    p = tmp_path / "rot.jpg"
    img = Image.new("RGB", (300, 100), "white")
    exif = img.getexif()
    exif[0x0112] = 6  # girar 90° para mostrar: el ancho y el alto se intercambian
    img.save(p, exif=exif)
    engine = FakeEngine()
    convert_image(str(p), engine)
    assert engine.seen[0].size == (100, 300)


def test_multiframe_tiff_processes_first_frame_and_warns(tmp_path):
    p = tmp_path / "m.tiff"
    frames = [Image.new("RGB", (100, 50), c) for c in ("white", "black", "red")]
    frames[0].save(p, save_all=True, append_images=frames[1:])
    engine = FakeEngine()
    result = convert_image(str(p), engine)
    assert len(engine.seen) == 1
    assert [(w.code, w.count) for w in result.warnings] == [("frames_skipped", 2)]


def test_engine_failure_propagates_with_context(tmp_path):
    class Boom(FakeEngine):
        def recognize(self, image):
            raise ConversionError("ocr_failed", "ocr", cause=RuntimeError("onnx"))

    with pytest.raises(ConversionError) as e:
        convert_image(png(tmp_path), Boom())
    assert e.value.code == "ocr_failed"
