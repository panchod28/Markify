# sidecar/build.py
"""
Script para compilar el sidecar Python con PyInstaller.
Ejecutar desde la raíz del proyecto: npm run build:sidecar
O directamente: cd sidecar && python build.py
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Carpeta --onedir que Tauri incluye en la app (ver tauri.macos.conf.json / tauri.windows.conf.json).
# El ejecutable queda en <OUTPUT_DIR>/markify-sidecar[.exe] y las librerías en <OUTPUT_DIR>/_internal/.
from fetch_ocr_models import MODELS_DIR, fetch as fetch_ocr_models

SIDECAR_NAME = "markify-sidecar"
OUTPUT_DIR = Path(__file__).parent.parent / "src-tauri" / "binaries" / SIDECAR_NAME


def setuptools_vendor_path() -> list[str]:
    """
    setuptools >= 71 vendoriza jaraco.* en setuptools/_vendor y el runtime hook
    pyi_rth_pkgres de PyInstaller no lo encuentra; lo añadimos al path de análisis.
    """
    spec = importlib.util.find_spec("setuptools")
    if spec is None or not spec.submodule_search_locations:
        return []
    vendor = Path(spec.submodule_search_locations[0]) / "_vendor"
    return ["--paths", str(vendor)] if (vendor / "jaraco").exists() else []


def build():
    work_dir = Path(__file__).parent / "build" / "work"
    dist_dir = OUTPUT_DIR.parent

    # Limpiar la salida anterior: un --onedir viejo mezclado con uno nuevo da fallos difíciles de rastrear.
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    print(f"-> Building sidecar (onedir) en {OUTPUT_DIR}")
    fetch_ocr_models()  # modelos OCR con SHA-256 verificado; nunca se descargan en runtime

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", SIDECAR_NAME,
        "--distpath", str(dist_dir),
        "--workpath", str(work_dir),
        "--specpath", str(Path(__file__).parent / "build"),
        "--clean",
        "--noconfirm",
        "--console",
        "--collect-submodules", "numpy._core",
        "--collect-submodules", "numpy.lib",
        "--collect-all", "magika",
        "--collect-all", "markitdown",
        "--collect-all", "PIL",
        "--copy-metadata", "python-pptx",
        "--copy-metadata", "markitdown",
        "--copy-metadata", "openpyxl",
        "--copy-metadata", "xlrd",
        "--collect-all", "pptx",
        "--hidden-import", "pptx",
        "--hidden-import", "pptx.oxml",
        "--hidden-import", "pptx.util",
        "--hidden-import", "pptx.dml.color",
        "--hidden-import", "pptx.parts.presentation",
        "--collect-data", "whisper",
        # OCR (rapidocr + modelos propios). Sin torch: el motor PyTorch de rapidocr no se usa.
        "--collect-all", "rapidocr",
        "--exclude-module", "rapidocr.inference_engine.pytorch",
        "--collect-binaries", "onnxruntime",
        "--add-data", f"{MODELS_DIR}{os.pathsep}ocr/models",
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "wx",
        "--exclude-module", "notebook",
        "--exclude-module", "IPython",
        "--additional-hooks-dir", str(Path(__file__).parent),
        *setuptools_vendor_path(),
        "main.py",
    ]

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent))

    if result.returncode != 0:
        print("x Build failed")
        sys.exit(1)

    # --collect-all rapidocr arrastra los modelos PP-OCRv6 del wheel (~31 MB) que no usamos.
    for unused in (OUTPUT_DIR / "_internal" / "rapidocr" / "models").glob("*.onnx"):
        unused.unlink()

    print(f"v Sidecar compilado exitosamente: {OUTPUT_DIR}")


if __name__ == "__main__":
    build()
