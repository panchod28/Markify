import io
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr import image_loader
from ocr.diagnostics import ConversionError
from ocr.image_loader import load_image


def png(img, fmt="PNG"):
    b = io.BytesIO()
    img.save(b, fmt)
    return b.getvalue()


def test_loads_from_bytes_and_from_a_path(tmp_path):
    data = png(Image.new("RGB", (120, 80), "red"))
    from_bytes, frames = load_image(data, "a.png")
    p = tmp_path / "a.png"
    p.write_bytes(data)
    from_path, _ = load_image(p, "a.png")
    assert from_bytes.mode == from_path.mode == "RGB" and from_bytes.size == from_path.size == (120, 80) and frames == 1


def test_transparency_is_composited_on_white():
    black_text_on_transparent = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    black_text_on_transparent.putpixel((5, 5), (0, 0, 0, 255))
    img, _ = load_image(png(black_text_on_transparent), "t.png")
    assert img.mode == "RGB" and img.getpixel((20, 20)) == (255, 255, 255) and img.getpixel((5, 5)) == (0, 0, 0)


def test_palette_png_with_transparency_is_composited_on_white():
    p = Image.new("P", (10, 10), 0)
    p.putpalette([0, 0, 0] * 256)
    p.info["transparency"] = 0
    b = io.BytesIO()
    p.save(b, "PNG", transparency=0)
    img, _ = load_image(b.getvalue(), "p.png")
    assert img.getpixel((3, 3)) == (255, 255, 255)


def test_large_images_are_reduced_keeping_the_aspect_ratio():
    img, _ = load_image(png(Image.new("RGB", (4000, 2000))), "big.png", max_side=1000)
    assert img.size == (1000, 500)


def test_small_images_are_not_enlarged():
    img, _ = load_image(png(Image.new("RGB", (300, 100))), "s.png")
    assert img.size == (300, 100)


def test_bytes_that_are_not_an_image_raise_decode_failed():
    with pytest.raises(ConversionError) as e:
        load_image(b"esto no es una imagen", "x.png")
    assert (e.value.code, e.value.stage, e.value.file) == ("image_decode_failed", "decode", "x.png")


def test_decompression_bomb_guard(monkeypatch):
    monkeypatch.setattr(image_loader, "MAX_PIXELS", 1000)
    with pytest.raises(ConversionError) as e:
        load_image(png(Image.new("RGB", (100, 100))), "b.png")
    assert e.value.code == "image_too_large"


def test_multiframe_gif_reports_its_frame_count():
    frames = [Image.new("RGB", (20, 20), c) for c in ("red", "green", "blue")]
    b = io.BytesIO()
    frames[0].save(b, "GIF", save_all=True, append_images=frames[1:])
    _, n = load_image(b.getvalue(), "m.gif")
    assert n == 3
