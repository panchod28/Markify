# sidecar/main.py
"""
Entry point del sidecar de Markify.
Lee comandos de stdin (JSON newline-delimited) y procesa según el tipo.
"""

import sys
import os

# Fix encoding para Windows: forzar UTF-8 en stdout/stdin
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')

# Asegurar que ffmpeg de Homebrew esté en PATH cuando la app se lanza desde Finder
if sys.platform == 'darwin':
    _extra = ['/opt/homebrew/bin', '/opt/homebrew/sbin', '/usr/local/bin']
    _path = os.environ.get('PATH', '')
    for _p in _extra:
        if _p not in _path and os.path.exists(_p):
            _path = _p + ':' + _path
    os.environ['PATH'] = _path

import threading
import traceback
from protocol import write_message
from dispatcher import run
from converter import convert_document
from whisper_handler import transcribe_audio
from model_manager import model_exists, download_model
from error_messages import get_error_message


_cancel_flag = threading.Event()


def main():
    """Conecta los handlers al despachador (lector de stdin + trabajador)."""
    run(
        handlers={
            "convert": handle_convert,
            "download_model": lambda _payload: handle_download_model(),
        },
        cancel_flag=_cancel_flag,
        model_available=model_exists,
    )


def handle_convert(payload: dict):
    """Procesa una lista de archivos secuencialmente."""
    files = payload.get("files", [])
    lang = payload.get("lang", "en")

    for file_info in files:
        if _cancel_flag.is_set():
            write_message({"type": "conversion_cancelled", "payload": {}})
            return

        file_id = file_info["id"]
        path = file_info["path"]
        category = file_info["category"]

        write_message({
            "type": "file_progress",
            "payload": {"fileId": file_id, "status": "processing", "progress": 0}
        })

        try:
            if category == "document":
                content = convert_document(path)
            elif category == "audio":
                content = transcribe_audio(path, file_id, _cancel_flag)
            else:
                raise ValueError(f"Categoría desconocida: {category}")

            if _cancel_flag.is_set():
                write_message({"type": "conversion_cancelled", "payload": {}})
                return

            write_message({
                "type": "file_result",
                "payload": {
                    "fileId": file_id,
                    "status": "completed",
                    "progress": 100,
                    "markdownContent": content,
                    "errorMessage": None
                }
            })

        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            error_msg = get_error_message(e, lang)
            write_message({
                "type": "file_result",
                "payload": {
                    "fileId": file_id,
                    "status": "error",
                    "progress": 0,
                    "markdownContent": None,
                    "errorMessage": error_msg
                }
            })

    if not _cancel_flag.is_set():
        write_message({"type": "conversion_complete", "payload": {}})


def handle_download_model():
    """Descarga el modelo de Whisper y emite progreso."""
    def progress_callback(percent: float, downloaded_mb: float, total_mb: float):
        write_message({
            "type": "model_progress",
            "payload": {
                "percent": int(percent),
                "downloadedMB": round(downloaded_mb, 1),
                "totalMB": round(total_mb, 1)
            }
        })

    try:
        download_model(progress_callback)
        write_message({"type": "model_ready", "payload": {}})
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        write_message({
            "type": "model_error",
            "payload": {"message": str(e)}
        })


if __name__ == "__main__":
    main()
