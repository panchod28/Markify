import re
from pathlib import Path

from error_messages import MESSAGES, WARNINGS

OCR_DIR = Path(__file__).parent.parent / "ocr"
SOURCES = "\n".join(p.read_text(encoding="utf-8") for p in OCR_DIR.glob("*.py"))


def test_every_error_code_raised_in_ocr_has_a_user_message_in_both_languages():
    codes = set(re.findall(r'ConversionError\(\s*"([a-z_]+)"', SOURCES))
    assert {"pdf_open_failed", "page_render_failed", "ocr_failed", "no_text_found"} <= codes
    for lang in ("es", "en"):
        assert codes <= set(MESSAGES[lang]), codes - set(MESSAGES[lang])


def test_every_warning_code_has_a_template_in_both_languages():
    codes = set(re.findall(r'PageIssue\(\s*"([a-z_]+)"', SOURCES))
    assert {"page_failed", "low_confidence_dropped", "frames_skipped"} <= codes
    for lang in ("es", "en"):
        assert codes <= set(WARNINGS[lang]), codes - set(WARNINGS[lang])
