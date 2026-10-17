# sidecar/ocr/base.py
"""Tipos compartidos por los motores OCR y sus consumidores (sin dependencias pesadas)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OcrLine:
    text: str
    box: tuple[float, float, float, float]  # (izquierda, arriba, derecha, abajo) en píxeles
    confidence: float                       # 0..1


class OcrEngine(Protocol):
    name: str

    def recognize(self, image) -> list[OcrLine]:
        """`image`: PIL.Image RGB. Lanza ConversionError(code="ocr_failed") si el motor falla."""
        ...
