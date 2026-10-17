# Spec 05 — Python Sidecar Protocol & Implementation
> Markify — Protocolo de comunicación stdin/stdout y código Python completo del sidecar.
> Archivos destino: `sidecar/` (directorio completo)
> El sidecar se empaqueta como binario con PyInstaller. Ver spec `10-build.md`.

---

## 1. Resumen del protocolo

- **Transporte:** stdin/stdout del proceso hijo (proceso Python lanzado por Tauri).
- **Formato:** JSON newline-delimited — cada mensaje es un JSON en **una sola línea** terminada en `\n`.
- **Dirección Tauri → Python:** stdin del proceso.
- **Dirección Python → Tauri:** stdout del proceso (stderr solo para logs internos, nunca para protocolo).
- **Concurrencia:** el sidecar procesa mensajes de forma secuencial. No hay paralelismo entre conversiones.

---

## 2. Mensajes Tauri → Python (stdin)

### 2.1 Iniciar conversión

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "command": "convert",
  "payload": {
    "files": [
      {
        "id": "file-uuid-1",
        "path": "/Users/juan/Documents/informe.pdf",
        "category": "document"
      },
      {
        "id": "file-uuid-2",
        "path": "/Users/juan/Music/grabacion.mp3",
        "category": "audio"
      }
    ],
    "lang": "es"
  }
}
```

- `id`: UUID v4 del mensaje (para trazabilidad interna).
- `files[].id`: UUID que el frontend asignó al archivo. **Devolver el mismo id en los mensajes de respuesta.**
- `files[].path`: ruta absoluta en el disco. No asumir que el archivo existe — verificar al procesar.
- `files[].category`: `"document"` o `"audio"`. No re-detectar — usar la categoría que envía Tauri.
- `lang`: `"es"` o `"en"`. Usar para seleccionar los mensajes de error correctos.

### 2.2 Cancelar conversión

```json
{
  "id": "...",
  "command": "cancel",
  "payload": {}
}
```

- Puede llegar en cualquier momento durante una conversión activa: un hilo lector de stdin lo atiende **al instante** (activa el flag) aunque el trabajador esté ocupado.
- El trabajo en curso debe consultar el flag: antes de cada archivo y, en audio, tras cada ventana de ~30 s de Whisper (ver `whisper_progress.py`). La latencia de cancelación de un audio es la de una ventana (medido: ~8 s en CPU Apple Silicon con el modelo `base`).
- Al detectar cancelación, emitir `conversion_cancelled` y dejar de procesar; no se emite `file_result` completado para el archivo interrumpido.
- El flag se limpia cuando se **encola** cada `convert` (no al ejecutarlo): un `cancel` posterior se conserva aunque el trabajo aún no haya empezado, y un `cancel` sin conversión activa no afecta al siguiente `convert`.

### 2.3 Verificar modelo Whisper

```json
{
  "id": "...",
  "command": "check_model",
  "payload": {}
}
```

### 2.4 Descargar modelo Whisper

```json
{
  "id": "...",
  "command": "download_model",
  "payload": {}
}
```

---

## 3. Mensajes Python → Tauri (stdout)

### 3.1 Progreso de un archivo

```json
{"type": "file_progress", "payload": {"fileId": "file-uuid-1", "status": "processing", "progress": 0}}
```

Emitir inmediatamente cuando se empieza a procesar un archivo.

### 3.2 Progreso parcial de transcripción (solo audio)

```json
{"type": "file_progress", "payload": {"fileId": "file-uuid-2", "status": "processing", "progress": 45}}
```

`progress` es un entero de 0 a 99. Nunca emitir 100 en `file_progress` — el 100 lo da `file_result`.

### 3.3 Archivo completado exitosamente

```json
{
  "type": "file_result",
  "payload": {
    "fileId": "file-uuid-1",
    "status": "completed",
    "progress": 100,
    "content": "# Informe de Ventas\n\nContenido del documento...",
    "errorMessage": null
  }
}
```

### 3.4 Archivo con error

```json
{
  "type": "file_result",
  "payload": {
    "fileId": "file-uuid-1",
    "status": "error",
    "progress": 0,
    "content": null,
    "errorMessage": "El archivo está protegido con contraseña"
  }
}
```

`errorMessage` ya debe estar en el idioma correcto (`lang` recibido en el comando `convert`).

### 3.5 Conversión completa

```json
{"type": "conversion_complete", "payload": {}}
```

Emitir después de procesar **todos** los archivos del batch (exitosos y con error).

### 3.6 Conversión cancelada

```json
{"type": "conversion_cancelled", "payload": {}}
```

Emitir cuando se detecta el flag de cancelación y se para el procesamiento.

### 3.7 Progreso de descarga del modelo

```json
{"type": "model_progress", "payload": {"percent": 34, "downloadedMB": 49.3, "totalMB": 145.0}}
```

`percent`: entero 0-100. `downloadedMB` y `totalMB`: float con 1 decimal.

### 3.8 Modelo listo

```json
{"type": "model_ready", "payload": {}}
```

### 3.9 Error descargando el modelo

```json
{"type": "model_error", "payload": {"message": "Sin conexión a internet. Verifica tu conexión e intenta de nuevo."}}
```

### 3.10 Estado del modelo (respuesta a check_model)

```json
{"type": "model_status", "request_id": "<id del comando check_model>", "payload": {"available": true}}
```

`request_id` es el `id` recibido en `check_model` (`null` si no venía). **Rust solo resuelve `check_whisper_model` si el mensaje lo trae**; sin él la comprobación expira. Se responde al instante, también durante una conversión.

---

## 4. Estructura de archivos del sidecar

```
sidecar/
├── main.py           ← Entry point + loop de lectura stdin
├── protocol.py       ← Lectura/escritura de mensajes JSON
├── converter.py      ← Conversión con markitdown
├── whisper_handler.py← Transcripción con Whisper
├── model_manager.py  ← Descarga y verificación del modelo Whisper
├── sanitizer.py      ← Sanitización de nombres de archivo
├── error_messages.py ← Mapeo de excepciones a mensajes de usuario
├── requirements.txt
└── build.py          ← Script PyInstaller
```

---

## 5. Implementación completa — `main.py`

```python
# sidecar/main.py
"""
Entry point del sidecar de Markify.
Lee comandos de stdin (JSON newline-delimited) y procesa según el tipo.
"""

import threading
from protocol import write_message
from dispatcher import run
from converter import convert_document
from whisper_handler import transcribe_audio
from model_manager import model_exists, download_model
from error_messages import get_error_message


# Flag global de cancelación — thread-safe
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

# dispatcher.py (sin imports pesados, testeable con handlers falsos):
#  - hilo lector: `cancel` -> _cancel_flag.set(); `check_model` -> model_status con request_id;
#    `convert` -> _cancel_flag.clear() y encolar; `download_model` -> encolar; EOF -> centinela.
#  - trabajador (hilo principal): ejecuta los trabajos encolados en orden.
#  - cada comando se despacha dentro de try/except: un error se registra en stderr y el lector sigue.
# protocol.write_message usa un Lock: lector y trabajador pueden escribir a la vez sin mezclar líneas.


def handle_convert(payload: dict):
    """Procesa una lista de archivos secuencialmente."""
    files = payload.get("files", [])
    lang = payload.get("lang", "en")

    for file_info in files:
        # Verificar cancelación antes de cada archivo
        if _cancel_flag.is_set():
            write_message({"type": "conversion_cancelled", "payload": {}})
            return

        file_id = file_info["id"]
        path = file_info["path"]
        category = file_info["category"]

        # Notificar que comenzamos
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

            # Verificar cancelación después de completar
            if _cancel_flag.is_set():
                write_message({"type": "conversion_cancelled", "payload": {}})
                return

            write_message({
                "type": "file_result",
                "payload": {
                    "fileId": file_id,
                    "status": "completed",
                    "progress": 100,
                    "content": content,
                    "errorMessage": None
                }
            })

        except Exception as e:
            error_msg = get_error_message(e, lang)
            write_message({
                "type": "file_result",
                "payload": {
                    "fileId": file_id,
                    "status": "error",
                    "progress": 0,
                    "content": None,
                    "errorMessage": error_msg
                }
            })

    # Solo emitir complete si no fue cancelado
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
        write_message({
            "type": "model_error",
            "payload": {"message": str(e)}
        })


if __name__ == "__main__":
    main()
```

---

## 6. Implementación — `protocol.py`

```python
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
```

---

## 7. Implementación — `converter.py`

```python
# sidecar/converter.py
"""
Conversión de documentos a Markdown usando markitdown.
"""

import os
from pathlib import Path
from markitdown import MarkItDown


# Instanciar una vez — es thread-safe y mantiene estado interno
_md_converter = MarkItDown()


def convert_document(file_path: str) -> str:
    """
    Convierte un documento al formato Markdown.

    Args:
        file_path: Ruta absoluta al archivo a convertir.

    Returns:
        Contenido Markdown como string.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        PermissionError: Si el archivo está bloqueado/protegido con contraseña.
        ValueError: Si el archivo está vacío o no contiene texto extraíble.
        RuntimeError: Para cualquier otro error de conversión.
    """
    path = Path(file_path)

    # Verificaciones previas
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    if path.stat().st_size == 0:
        raise ValueError("El archivo está vacío")

    try:
        result = _md_converter.convert(file_path)
        content = result.text_content

        if not content or not content.strip():
            raise ValueError("No se encontró texto en el archivo")

        return content

    except PermissionError:
        # markitdown lanza PermissionError para archivos con contraseña
        raise PermissionError("Archivo protegido con contraseña")

    except (FileNotFoundError, ValueError, PermissionError):
        # Re-lanzar excepciones conocidas sin envolver
        raise

    except Exception as e:
        # Envolver excepciones desconocidas de markitdown
        error_str = str(e).lower()
        if "password" in error_str or "encrypted" in error_str:
            raise PermissionError("Archivo protegido con contraseña")
        if "corrupt" in error_str or "invalid" in error_str:
            raise RuntimeError("file_corrupted")
        raise RuntimeError(f"unknown: {e}")
```

---

## 8. Implementación — `whisper_handler.py`

```python
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

    # Cargar el modelo (ya debe estar descargado — verificado antes de llegar aquí)
    model = whisper.load_model("base", download_root=str(get_model_path()))

    # Verificar cancelación
    if cancel_flag.is_set():
        return ""

    def report(pct: int):
        write_message({
            "type": "file_progress",
            "payload": {"fileId": file_id, "status": "processing", "progress": pct}
        })

    # verbose=None: con False Whisper imprime "Detected language: ..." en stdout y rompería
    # el protocolo JSON. El progreso real (0-99) y la cancelación llegan por hook_progress, que
    # sustituye el tqdm de whisper.transcribe mientras dura la llamada (ver whisper_progress.py).
    try:
        with hook_progress(_transcribe_module(), cancel_flag, report):
            result = model.transcribe(
                file_path,
                verbose=None,
                language=None,  # Detección automática del idioma del audio
                fp16=False,     # Usar FP32 para compatibilidad CPU
            )
    except TranscriptionCancelled:
        return ""
    except Exception as e:
        error_str = str(e).lower()
        if "no speech" in error_str or "too short" in error_str:
            raise ValueError("audio_too_short")
        raise RuntimeError(f"unknown: {e}")

    # Extraer texto
    text = result.get("text", "").strip()
    if not text:
        raise ValueError("audio_too_short")

    # Verificar cancelación después de transcribir
    if cancel_flag.is_set():
        return ""

    # Formatear como Markdown
    filename_stem = path.stem
    markdown_content = f"""# Transcripción: {filename_stem}

> Transcripción generada automáticamente con Whisper (modelo: base)
> Archivo original: {path.name}

---

{text}
"""

    return markdown_content
```

---

## 9. Implementación — `model_manager.py`

```python
# sidecar/model_manager.py
"""
Gestión del modelo de Whisper: verificación, descarga y ruta de almacenamiento.
"""

import os
import sys
import urllib.request
from pathlib import Path
from typing import Callable


# Nombre del modelo — NO cambiar en v1
WHISPER_MODEL_NAME = "base"

# URL de descarga del modelo (repositorio oficial de Whisper)
# El modelo 'base' se llama 'base.pt' internamente
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
        # Ejecutando como PyInstaller bundle
        base = Path(sys.executable).parent
    else:
        # Desarrollo
        base = Path.home() / ".markify"

    model_dir = base / "models" / "whisper"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def model_exists() -> bool:
    """Verifica si el archivo del modelo existe y tiene el tamaño correcto."""
    model_file = get_model_path() / WHISPER_MODEL_FILENAME
    if not model_file.exists():
        return False
    # Verificar que el tamaño es razonable (>100MB = descarga completa)
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
        # Limpiar archivo parcial
        if model_file.exists():
            model_file.unlink()
        raise ConnectionError(
            "Sin conexión a internet. Verifica tu conexión e intenta de nuevo."
        ) from e

    except Exception as e:
        if model_file.exists():
            model_file.unlink()
        raise RuntimeError(f"Error descargando el modelo: {e}") from e
```

---

## 10. Implementación — `error_messages.py`

```python
# sidecar/error_messages.py
"""
Mapeo de excepciones Python a mensajes de error legibles para el usuario.
"""

MESSAGES = {
    "es": {
        "FileNotFoundError":  "No se pudo encontrar el archivo",
        "PermissionError":    "El archivo está protegido con contraseña",
        "file_corrupted":     "No se pudo leer el archivo (puede estar dañado)",
        "ValueError_empty":   "No se encontró texto en el archivo",
        "audio_too_short":    "El audio es muy corto o no contiene voz detectada",
        "ConnectionError":    "Sin conexión a internet. Verifica tu conexión e intenta de nuevo.",
        "unknown":            "Error inesperado al convertir el archivo",
    },
    "en": {
        "FileNotFoundError":  "Could not find the file",
        "PermissionError":    "The file is password protected",
        "file_corrupted":     "Could not read the file (it may be corrupted)",
        "ValueError_empty":   "No text was found in the file",
        "audio_too_short":    "The audio is too short or contains no detected speech",
        "ConnectionError":    "No internet connection. Check your connection and try again.",
        "unknown":            "Unexpected error while converting the file",
    }
}


def get_error_message(exception: Exception, lang: str = "en") -> str:
    """
    Convierte una excepción a un mensaje de error legible para el usuario.

    Args:
        exception: La excepción capturada.
        lang: Idioma del mensaje ('es' o 'en'). Default: 'en'.

    Returns:
        String con el mensaje de error en el idioma solicitado.
    """
    msgs = MESSAGES.get(lang, MESSAGES["en"])
    exc_type = type(exception).__name__
    exc_str = str(exception)

    # Excepciones específicas
    if exc_type == "FileNotFoundError":
        return msgs["FileNotFoundError"]

    if exc_type == "PermissionError":
        return msgs["PermissionError"]

    if exc_type == "ConnectionError":
        return msgs["ConnectionError"]

    if exc_type == "ValueError":
        if "audio_too_short" in exc_str:
            return msgs["audio_too_short"]
        return msgs["ValueError_empty"]

    if exc_type == "RuntimeError":
        if "file_corrupted" in exc_str:
            return msgs["file_corrupted"]
        if "audio_too_short" in exc_str:
            return msgs["audio_too_short"]

    return msgs["unknown"]
```

---

## 11. Implementación — `sanitizer.py`

> Ver spec `09-pipeline.md` § Sanitización para la implementación completa.
> Este módulo es usado internamente por el sidecar para validar nombres, no para la salida (el frontend ya sanitizó).

```python
# sidecar/sanitizer.py
import re
import unicodedata
from pathlib import Path


def sanitize_filename(original_name: str) -> str:
    """
    Convierte el nombre de un archivo a una versión segura .md.
    Ver spec 09-pipeline.md para la tabla de ejemplos y el algoritmo completo.
    """
    stem = Path(original_name).stem
    normalized = unicodedata.normalize("NFKD", stem)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    lower = ascii_str.lower()
    underscored = re.sub(r"[\s\-\.]+", "_", lower)
    clean = re.sub(r"[^a-z0-9_]", "", underscored)
    clean = re.sub(r"_+", "_", clean).strip("_")
    return f"{clean or 'archivo_sin_nombre'}.md"
```

---

## 12. `requirements.txt`

```
markitdown==0.1.0
openai-whisper
torch==2.3.1+cpu
torchaudio==2.3.1+cpu
--find-links https://download.pytorch.org/whl/torch_stable.html
PyInstaller==6.8.0
```

> **Nota sobre torch:** Usar la variante `+cpu` para evitar las dependencias de CUDA y reducir el tamaño del bundle. El sidecar nunca intenta usar GPU — siempre `fp16=False` en Whisper.

---

## 13. Reglas de protocolo críticas

1. **Nunca escribir nada al stdout que no sea JSON válido seguido de `\n`.** Cualquier `print()` debug debe ir a `sys.stderr`.
2. **Siempre hacer `sys.stdout.flush()` después de cada `write_message()`.** Si no se hace flush, Tauri no recibe el mensaje hasta que el buffer llena.
3. **El campo `fileId` en los mensajes de respuesta debe ser exactamente el mismo `id` que llegó en el payload.** Sin transformaciones.
4. **Emitir `conversion_complete` o `conversion_cancelled` exactamente UNA VEZ** al terminar un batch, nunca cero veces ni más de una.
5. **Si el sidecar falla internamente (crash):** Tauri detecta que el proceso terminó y emite error en todos los archivos pendientes. El sidecar no necesita manejar este caso — Tauri lo hace.
6. **No mantener estado entre conversiones:** cada mensaje `convert` es independiente. No asumir nada del batch anterior.
