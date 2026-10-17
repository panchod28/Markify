# sidecar/gen_licenses.py
"""
Genera ../THIRD_PARTY_LICENSES.txt con los textos completos de licencia (LICENSE/NOTICE/COPYING de cada
distribución) de las dependencias de OCR que viajan en el instalador. Ejecutar tras cambiar esas dependencias:
    python gen_licenses.py        # usa el entorno de build; falla si a una distribución le falta el texto
"""

import sys
from importlib import metadata
from pathlib import Path

OUT = Path(__file__).parent.parent / "THIRD_PARTY_LICENSES.txt"
DISTS = ["rapidocr", "onnxruntime", "opencv-python-headless", "pypdfium2", "pdfminer.six", "shapely", "pyclipper", "Pillow"]
NAMES = ("LICENSE", "LICENCE", "COPYING", "NOTICE", "AUTHORS")


def texts(dist: str) -> list[tuple[str, str]]:
    d = metadata.distribution(dist)
    found = []
    for f in d.files or []:
        if f.name.upper().split(".")[0] in NAMES or f.parent.name.lower() == "licenses":
            found.append((str(f), f.locate().read_text(encoding="utf-8", errors="replace").strip()))
    return found


def main() -> int:
    parts = ["Full license texts of the OCR components shipped with Markify (see THIRD_PARTY_NOTICES.md).\n"
             "The PP-OCRv5 models (PaddleOCR) are Apache-2.0, the same license as RapidOCR below.\n"]
    missing = []
    for dist in DISTS:
        found = texts(dist)
        if not found:
            missing.append(dist)
            continue
        parts.append(f"\n{'=' * 78}\n{dist} {metadata.version(dist)}\n{'=' * 78}")
        seen = set()
        for name, body in found:
            if body and body not in seen:  # los wheels repiten el mismo texto en varias rutas
                seen.add(body)
                parts.append(f"\n--- {name} ---\n{body}")
    if missing:
        print(f"Sin texto de licencia en: {', '.join(missing)}", file=sys.stderr)
        return 1
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
