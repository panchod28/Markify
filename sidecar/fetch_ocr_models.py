# sidecar/fetch_ocr_models.py
"""
Descarga los modelos OCR (solo en build/CI, nunca en runtime) a sidecar/ocr/models/ y verifica su SHA-256.
Ejecutar: python fetch_ocr_models.py   (build.py lo llama antes de empaquetar; es idempotente)
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "ocr" / "models"
BASE_URL = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv5"

# nombre -> (ruta relativa en BASE_URL, SHA-256). Versión y hash fijados: si cambian, el build falla.
MODELS = {
    "ch_PP-OCRv5_det_mobile.onnx": (
        "det/ch_PP-OCRv5_det_mobile.onnx",
        "4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae",
    ),
    "latin_PP-OCRv5_rec_mobile.onnx": (
        "rec/latin_PP-OCRv5_rec_mobile.onnx",
        "b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, (rel, expected) in MODELS.items():
        target = MODELS_DIR / name
        if target.exists() and sha256(target) == expected:
            print(f"ok   {name}")
            continue
        print(f"get  {name}")
        tmp = target.with_suffix(".part")
        urllib.request.urlretrieve(f"{BASE_URL}/{rel}", tmp)
        got = sha256(tmp)
        if got != expected:
            tmp.unlink(missing_ok=True)
            raise SystemExit(f"SHA-256 inválido para {name}: esperado {expected}, obtenido {got}")
        tmp.replace(target)


if __name__ == "__main__":
    try:
        fetch()
    except Exception as e:
        print(f"x No se pudieron obtener los modelos OCR: {e}", file=sys.stderr)
        sys.exit(1)
