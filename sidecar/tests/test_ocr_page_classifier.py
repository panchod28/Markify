import pytest

from ocr.page_classifier import (
    IMAGE_MIN_AREA, MIN_TEXT_CHARS, SCAN_COVERAGE, PageKind as K, PageMetrics as M, classify_page,
)


def test_thresholds_are_the_calibrated_ones():
    assert (MIN_TEXT_CHARS, IMAGE_MIN_AREA, SCAN_COVERAGE) == (25, 0.05, 0.5)


@pytest.mark.parametrize("metrics, expected", [
    # (caracteres, cobertura total, imagen más grande)
    (M(800, 0.0, 0.0), K.TEXT),             # página de texto
    (M(0, 0.95, 0.95), K.SCANNED),          # escaneada
    (M(480, 1.0, 1.0), K.TEXT),             # escaneo con capa de texto previa: manda la capa
    (M(480, 0.2, 0.2), K.MIXED),            # texto + figura
    (M(480, 0.01, 0.01), K.TEXT),           # texto + logo
    (M(0, 0.0, 0.0), K.BLANK),              # en blanco
    # fronteras de MIN_TEXT_CHARS
    (M(25, 0.0, 0.0), K.TEXT),
    (M(24, 0.0, 0.0), K.TEXT),              # poco texto y sin imágenes: no es escaneo ni blanco
    (M(24, 0.5, 0.5), K.SCANNED),
    (M(25, 0.5, 0.5), K.TEXT),
    # fronteras de IMAGE_MIN_AREA
    (M(25, 0.05, 0.05), K.MIXED),
    (M(25, 0.0499, 0.0499), K.TEXT),
    (M(0, 0.05, 0.05), K.SCANNED),
    (M(0, 0.0499, 0.0499), K.BLANK),        # solo un logo y sin texto
    # fronteras de SCAN_COVERAGE
    (M(25, 0.49, 0.49), K.MIXED),
    (M(0, 0.5, 0.5), K.SCANNED),
    (M(0, 0.49, 0.49), K.SCANNED),          # imagen relevante sin texto
    # escaneo en franjas: ninguna imagen domina pero juntas cubren la página
    (M(0, 0.9, 0.1), K.SCANNED),
    (M(300, 0.9, 0.1), K.TEXT),
    # decoración repartida: varias imágenes pequeñas que no son un escaneo
    (M(300, 0.04, 0.02), K.TEXT),
])
def test_classify_page(metrics, expected):
    assert classify_page(metrics) is expected
