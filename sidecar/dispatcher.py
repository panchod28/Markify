# sidecar/dispatcher.py
"""
Despacho de comandos del sidecar: un hilo lee stdin y un trabajador ejecuta los trabajos largos.

- `cancel` y `check_model` se atienden en el lector, al instante, aunque el trabajador esté ocupado.
- `convert` y `download_model` se encolan y los ejecuta el trabajador (hilo que llama a `run`) en orden.

Sin imports pesados (torch/whisper): los handlers se inyectan desde main.py, así se prueba con handlers falsos.
"""

import json
import queue
import sys
import threading
import traceback
from typing import Callable

from protocol import read_message, write_message

_STOP = object()


def _log(msg: str) -> None:
    print(f"[Sidecar] {msg}", file=sys.stderr)


def _read_loop(
    jobs: "queue.Queue",
    cancel_flag: threading.Event,
    model_available: Callable[[], bool],
    read: Callable[[], dict],
    write: Callable[[dict], None],
) -> None:
    try:
        while True:
            try:
                msg = read()
            except EOFError:
                break
            except json.JSONDecodeError as e:
                _log(f"JSON inválido recibido: {e}")
                continue
            except Exception as e:
                _log(f"Error inesperado leyendo mensaje: {e}")
                traceback.print_exc(file=sys.stderr)
                continue

            command = msg.get("command")
            try:
                if command == "cancel":
                    cancel_flag.set()

                elif command == "check_model":
                    write({
                        "type": "model_status",
                        "request_id": msg.get("id"),
                        "payload": {"available": model_available()},
                    })

                elif command == "convert":
                    # Limpiar al encolar (no al ejecutar): un cancel posterior, aunque llegue antes de
                    # que el trabajador empiece, se conserva; un cancel ocioso no afecta a este convert.
                    cancel_flag.clear()
                    jobs.put((command, msg["payload"]))

                elif command == "download_model":
                    jobs.put((command, msg.get("payload")))

                else:
                    _log(f"Comando desconocido: {command}")

            except Exception as e:
                _log(f"Error procesando comando '{command}': {e}")
                traceback.print_exc(file=sys.stderr)
    finally:
        jobs.put(_STOP)  # EOF: el trabajador termina los trabajos ya encolados y sale


def run(
    handlers: dict[str, Callable[[dict], None]],
    cancel_flag: threading.Event,
    model_available: Callable[[], bool],
    read: Callable[[], dict] = read_message,
    write: Callable[[dict], None] = write_message,
) -> None:
    """Bloquea ejecutando los trabajos encolados hasta que stdin se cierra y la cola se vacía."""
    jobs: "queue.Queue" = queue.Queue()
    reader = threading.Thread(
        target=_read_loop, args=(jobs, cancel_flag, model_available, read, write), daemon=True
    )
    reader.start()

    while True:
        job = jobs.get()
        if job is _STOP:
            break
        command, payload = job
        try:
            handlers[command](payload)
        except Exception as e:
            _log(f"Error procesando comando '{command}': {e}")
            traceback.print_exc(file=sys.stderr)
