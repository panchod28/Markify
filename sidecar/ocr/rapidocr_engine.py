# sidecar/ocr/rapidocr_engine.py
"""
Motor por defecto: RapidOCR sobre ONNX Runtime (CPU), modelos PP-OCRv5 incluidos en el binario:
detección `ch_PP-OCRv5_det_mobile` + reconocimiento `latin_PP-OCRv5_rec_mobile` (cubre español e inglés).
Ver el design del change add-ocr-image-pdf-support (resultados del spike).
"""

from ocr.base import OcrLine
from ocr.diagnostics import ConversionError
from ocr.resources import resource_path

DET_MODEL = "ch_PP-OCRv5_det_mobile.onnx"
REC_MODEL = "latin_PP-OCRv5_rec_mobile.onnx"


class RapidOcrEngine:
    name = "rapidocr"

    def __init__(self, models_dir=None):
        base = models_dir or resource_path("ocr", "models")
        det, rec = base / DET_MODEL, base / REC_MODEL
        missing = [p.name for p in (det, rec) if not p.exists()]
        if missing:
            raise ConversionError(
                "ocr_engine_unavailable", "ocr",
                cause=FileNotFoundError(f"modelos OCR ausentes: {', '.join(missing)}"),
            )
        try:
            # Importaciones aquí, no a nivel de módulo: cargar OpenCV/ONNX solo cuando se necesita OCR.
            from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR

            self._ocr = RapidOCR(params={
                # Rutas explícitas: sin ellas rapidocr descargaría modelos en su primer uso.
                "Det.model_path": str(det), "Det.ocr_version": OCRVersion.PPOCRV5, "Det.model_type": ModelType.MOBILE,
                "Rec.model_path": str(rec), "Rec.ocr_version": OCRVersion.PPOCRV5, "Rec.model_type": ModelType.MOBILE,
                "Rec.lang_type": LangRec.LATIN,
                # El clasificador de línea desordena páginas rectas (ver spike): la orientación es de página.
                "Global.use_cls": False,
                # La detección trabaja con el lado mayor <= 1280 px. Por defecto (`min` 736) una página A4 a 150 DPI
                # entra entera y el pico de RAM sube a ~1.9 GB; con 1280 baja a ~1.0 GB sin perder CER (texto de 7–10 pt).
                "Det.limit_type": "max", "Det.limit_side_len": 1280,
                # Devolver todas las líneas: el filtrado por confianza (y su aviso) lo hace layout.py.
                "Global.text_score": 0.0,
                "Global.log_level": "warning",
            })
        except Exception as e:
            raise ConversionError("ocr_engine_unavailable", "ocr", cause=e)

    def recognize(self, image) -> list[OcrLine]:
        import numpy as np

        try:
            bgr = np.asarray(image.convert("RGB"))[:, :, ::-1].copy()  # RapidOCR espera BGR (OpenCV)
            result = self._ocr(bgr)
        except Exception as e:
            raise ConversionError("ocr_failed", "ocr", cause=e)
        if result.txts is None:
            return []
        lines = []
        for box, text, score in zip(result.boxes, result.txts, result.scores):
            xs, ys = box[:, 0], box[:, 1]
            lines.append(OcrLine(text, (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())), float(score)))
        return lines
