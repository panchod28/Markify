# sidecar/whisper_handler.py
"""
Transcripción de audio/video a Markdown usando Whisper (modo local).
"""

import threading
from pathlib import Path
from model_manager import get_model_path
from protocol import write_message
import whisper


def transcribe_audio(
    file_path: str,
    file_id: str,
    cancel_flag: threading.Event
) -> str:
    """
    Transcribe un archivo de audio/video a Markdown.

    Args:
        file_path: Ruta absoluta al archivo de audio.
        file_id: ID del archivo (para emitir progreso parcial).
        cancel_flag: Event que se activa si el usuario cancela.

    Returns:
        Contenido Markdown con la transcripción formateada.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el audio es muy corto o no contiene voz.
        RuntimeError: Para errores inesperados de Whisper.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    if path.stat().st_size == 0:
        raise ValueError("El archivo de audio está vacío")

    model = whisper.load_model("base", download_root=str(get_model_path()))

    if cancel_flag.is_set():
        return ""

    try:
        result = model.transcribe(
            file_path,
            verbose=False,
            language=None,
            fp16=False,
        )
    except Exception as e:
        error_str = str(e).lower()
        if "no speech" in error_str or "too short" in error_str:
            raise ValueError("audio_too_short")
        raise RuntimeError(f"unknown: {e}")

    text = result.get("text", "").strip()
    if not text:
        raise ValueError("audio_too_short")

    write_message({
        "type": "file_progress",
        "payload": {"fileId": file_id, "status": "processing", "progress": 50}
    })

    if cancel_flag.is_set():
        return ""

    filename_stem = path.stem
    markdown_content = f"""# Transcripción: {filename_stem}

> Transcripción generada automáticamente con Whisper (modelo: base)
> Archivo original: {path.name}

---

{text}
"""

    return markdown_content
