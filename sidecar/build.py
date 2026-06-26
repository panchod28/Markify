# sidecar/build.py
"""
Script para compilar el sidecar Python con PyInstaller.
Ejecutar desde la raíz del proyecto: npm run build:sidecar
O directamente: cd sidecar && python build.py
"""

import subprocess
import sys
import platform
from pathlib import Path


def get_target_triple() -> str:
    """
    Retorna el target triple de la plataforma actual.
    Debe coincidir con el nombre que Tauri espera en src-tauri/binaries/.
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        if machine == "arm64":
            return "aarch64-apple-darwin"
        return "x86_64-apple-darwin"
    elif system == "Windows":
        return "x86_64-pc-windows-msvc"
    elif system == "Linux":
        return "x86_64-unknown-linux-gnu"
    else:
        raise RuntimeError(f"Plataforma no soportada: {system}")


def build():
    target = get_target_triple()
    ext = ".exe" if platform.system() == "Windows" else ""
    binary_name = f"markify-sidecar-{target}{ext}"
    output_dir = Path(__file__).parent.parent / "src-tauri" / "binaries"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"-> Building sidecar para {target}...")
    print(f"-> Output: {output_dir / binary_name}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", binary_name,
        "--distpath", str(output_dir),
        "--workpath", str(Path(__file__).parent / "build" / "work"),
        "--specpath", str(Path(__file__).parent / "build"),
        "--clean",
        "--noconfirm",
        "--console",
        "--collect-submodules", "numpy",
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
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "wx",
        "--exclude-module", "notebook",
        "--exclude-module", "IPython",
        "--additional-hooks-dir", str(Path(__file__).parent),
        "main.py",
    ]

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent))

    if result.returncode != 0:
        print("x Build failed")
        sys.exit(1)

    print(f"v Sidecar compilado exitosamente: {output_dir / binary_name}")


if __name__ == "__main__":
    build()
