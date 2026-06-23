# sidecar/protocol.py
"""
Lectura y escritura de mensajes JSON newline-delimited en stdin/stdout.
"""

import sys
import json


def read_message() -> dict:
    """
    Lee una línea de stdin y la parsea como JSON.
    Bloquea hasta recibir una línea.
    Lanza EOFError si stdin se cierra (Tauri terminó).
    Lanza json.JSONDecodeError si el JSON es inválido.
    """
    line = sys.stdin.readline()
    if not line:
        raise EOFError("stdin cerrado")
    return json.loads(line.strip())


def write_message(message: dict) -> None:
    """
    Serializa un dict a JSON y lo escribe en stdout con \n.
    Hace flush inmediato — crítico para que Tauri reciba el mensaje.
    """
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()
