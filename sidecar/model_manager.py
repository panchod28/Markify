# sidecar/model_manager.py
"""
Gestión del modelo de Whisper: verificación, descarga y ruta de almacenamiento.
"""

import sys
import urllib.request
from pathlib import Path
from typing import Callable


WHISPER_MODEL_NAME = "base"
WHISPER_MODEL_URL = "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt"
WHISPER_MODEL_FILENAME = "base.pt"
WHISPER_MODEL_SIZE_MB = 145.0


def get_model_path() -> Path:
    """
    Retorna la ruta a la carpeta donde se almacena el modelo de Whisper.

    En producción (PyInstaller): junto al binario del sidecar.
    En desarrollo: ~/.markify/models/

    La carpeta se crea si no existe.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path.home() / ".markify"

    model_dir = base / "models" / "whisper"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def model_exists() -> bool:
    """Verifica si el archivo del modelo existe y tiene el tamaño correcto."""
    model_file = get_model_path() / WHISPER_MODEL_FILENAME
    if not model_file.exists():
        return False
    size_mb = model_file.stat().st_size / (1024 * 1024)
    return size_mb > 100


def download_model(progress_callback: Callable[[float, float, float], None]) -> None:
    """
    Descarga el modelo de Whisper con reporte de progreso.

    Args:
        progress_callback: función(percent, downloaded_mb, total_mb)

    Raises:
        ConnectionError: Si no hay conexión a internet.
        RuntimeError: Para otros errores de descarga.
    """
    model_file = get_model_path() / WHISPER_MODEL_FILENAME

    try:
        def reporthook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            total = total_size if total_size > 0 else int(WHISPER_MODEL_SIZE_MB * 1024 * 1024)
            percent = min(100.0, downloaded / total * 100)
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            progress_callback(percent, downloaded_mb, total_mb)

        urllib.request.urlretrieve(WHISPER_MODEL_URL, str(model_file), reporthook)

    except urllib.error.URLError as e:
        if model_file.exists():
            model_file.unlink()
        raise ConnectionError(
            "Sin conexión a internet. Verifica tu conexión e intenta de nuevo."
        ) from e

    except Exception as e:
        if model_file.exists():
            model_file.unlink()
        raise RuntimeError(f"Error descargando el modelo: {e}") from e
