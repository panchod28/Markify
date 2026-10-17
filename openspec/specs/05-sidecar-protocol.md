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

**PDF con páginas escaneadas o mixtas:** también emite `file_progress` tras cada página, con `progress = 100 · páginas procesadas / total` (tope 99). Los mensajes de progreso nunca llevan `warnings` ni `markdownContent`. Los PDFs que van por la ruta rápida (todo texto) no emiten progreso intermedio.

### 3.3 Archivo completado exitosamente

```json
{
  "type": "file_result",
  "payload": {
    "fileId": "file-uuid-1",
    "status": "completed",
    "progress": 100,
    "markdownContent": "# Informe de Ventas\n\nContenido del documento...",
    "errorMessage": null
  }
}
```

**`warnings` (opcional):** si la conversión terminó con avisos no fatales, el payload añade
`"warnings": [{"page": 7, "stage": "render", "code": "page_failed", "message": "La página 7 no se pudo procesar"}]`.
Si no hay avisos el campo se **omite** (no se envía vacío). `page` es `null` en avisos de todo el archivo; `message` va localizado según `lang`. Códigos de aviso: `page_failed`, `low_confidence_dropped`, `frames_skipped`, `image_failed` (imagen de DOCX/PPTX; con `page` = diapositiva en PPTX) e `images_skipped`. Rust y el frontend lo reenvían sin interpretarlo.

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
├── error_messages.py ← Mapeo de excepciones/códigos a mensajes de usuario (ES/EN)
├── ocr/              ← OCR local (ver §14); se importa bajo demanda
├── fetch_ocr_models.py ← Descarga los modelos OCR con SHA-256 fijado (solo build/CI)
├── smoke_test.py     ← Prueba del binario empaquetado
├── tests/            ← pytest
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
markitdown[all]==0.1.6
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

7. **`print()` está prohibido en todo el sidecar, incluido `ocr/`.** Los diagnósticos van a stderr (`ocr/diagnostics.py::log_issue`: una línea por incidente con archivo, página, etapa y código; sin rutas completas ni contenido del documento).
8. **Las importaciones de OCR son siempre perezosas** (dentro de la función o rama que las usa): convertir un documento de texto o audio nunca carga OpenCV ni ONNX.

---

## 14. OCR, imágenes y PDF por página (`sidecar/ocr/`)

> Introducido por el change `add-ocr-image-pdf-support`. El código vigente es `sidecar/ocr/`; aquí se fijan las reglas y el contrato.

### 14.1 Despacho en `handle_convert`

| `category` / extensión | Handler |
|---|---|
| `document`, extensión `.pdf` | `ocr.pdf_pipeline.convert_pdf(path, cancel_flag, on_progress)` |
| `document`, extensión `.docx` | `ocr.office_images.convert_docx(path, cancel_flag, on_progress)` |
| `document`, extensión `.pptx` | `ocr.office_images.convert_pptx(path, cancel_flag, on_progress)` |
| `document`, `.doc` / `.ppt` | `convert_document` lanza `ConversionError("legacy_format")` (el frontend ya los rechaza) |
| `document`, resto | `convert_document(path)` (sin cambios) |
| `audio` | `transcribe_audio(...)` |
| `image` | `ocr.image_converter.convert_image(path)` |

`convert_image`, `convert_pdf`, `convert_docx` y `convert_pptx` devuelven `ConversionResult(markdown, warnings: list[PageIssue])`; `main.py` serializa los avisos con `error_messages.issue_to_payload(issue, lang)`.

### 14.2 Motor OCR

- `ocr/engine.py`: `OcrEngine` (Protocol con `recognize(image) -> list[OcrLine]`), `ENGINES` y `get_engine()` (singleton perezoso; `MARKIFY_OCR_ENGINE` solo para desarrollo). Añadir un motor = una clase + una línea en `ENGINES`.
- Motor por defecto `rapidocr_engine.py`: RapidOCR sobre ONNX Runtime (CPU), PP-OCRv5 `det mobile` + `rec latin mobile`, **sin** clasificador de línea, con rutas de modelo explícitas (nunca descarga en runtime) y detección con `limit_type=max`, `limit_side_len=1280` (pico de RAM ≈ 1.1 GB; con el valor por defecto de RapidOCR llega a ≈ 1.9 GB).
- Los modelos se obtienen en build con `fetch_ocr_models.py` (versión y SHA-256 fijados) a `sidecar/ocr/models/` y viajan dentro del binario (`ocr/resources.py::resource_path`, `sys._MEIPASS` cuando está empaquetado).

### 14.3 Clasificación y pipeline de PDF

`page_classifier.classify_page(PageMetrics)` es pura. Umbrales: `MIN_TEXT_CHARS=25`, `IMAGE_MIN_AREA=0.05`, `SCAN_COVERAGE=0.5`.

| Clase | Condición | Tratamiento |
|---|---|---|
| `TEXT` | ≥ 25 caracteres y sin imagen relevante, o capa de texto con imagen de página completa | texto nativo (pdfminer) |
| `SCANNED` | < 25 caracteres y (imágenes cubren ≥ 50 % o alguna ≥ 5 %) | render 150 DPI (lado mayor ≤ 1 800 px, una página en memoria) + OCR + `layout` |
| `MIXED` | ≥ 25 caracteres e imagen ≥ 5 % que no cubre la página | texto nativo + OCR del recorte de cada imagen relevante, después del texto |
| `BLANK` | sin texto ni imágenes relevantes | se omite sin aviso |

- **Ruta rápida:** todo `TEXT`/`BLANK` → `convert_document` tal cual (salida idéntica byte a byte; no se carga el motor).
- **Ruta híbrida:** alguna `SCANNED`/`MIXED`; páginas unidas en orden con una línea en blanco.
- **Orientación:** `/Rotate` lo resuelve pdfium al renderizar. Si a 0° no se lee texto horizontal en una página `SCANNED`, se reintenta a 90/180/270° y se conserva la de mayor suma `confianza × longitud`; solo cuentan las líneas horizontales. Si ninguna lee texto, la página falla con `ocr_failed`.
- **Fallos por página:** un único `try/except` por página; produce `PageIssue("page_failed", etapa, página)`, el marcador `<!-- Markify: página N no se pudo procesar (código) -->` (el código es el de la causa) y continúa. Si ninguna página aporta texto: error con el código del primer fallo, o `no_text_found` si no hubo fallos.
- **Errores fatales del archivo:** cifrado → `PermissionError("Archivo protegido con contraseña")` (mismo mensaje de siempre); `pdf_open_failed` (no abrible, truncado, 0 páginas); `ocr_engine_unavailable`.
- **Cancelación y progreso:** `cancel_flag` se consulta antes de cada página; al cancelar, `convert_pdf` devuelve `""` y `main.py` emite `conversion_cancelled`. `on_progress` recibe 0–99 (§3.2).

### 14.4 Layout (`ocr/layout.py::lines_to_markdown`)

Filtra por `MIN_CONFIDENCE=0.5` (devuelve cuántas líneas descartó; se avisa **una vez por archivo** con `low_confidence_dropped`), detecta columnas por huecos en la proyección horizontal (hueco mínimo = 1.0 × la altura mediana de caja, porque las cajas del detector vienen infladas; tolera hasta ~5 % de líneas puente —título, encabezado o pie centrados— que se colocan antes/después de las columnas), ordena de arriba abajo y une líneas en párrafos. No infiere encabezados, tablas ni listas.

### 14.5 Errores y diagnóstico (`ocr/diagnostics.py`)

`ConversionError(code, stage, file, page, cause)` con `code` estable; `get_error_message` resuelve primero `exception.code` en `MESSAGES[lang]` y, si no está, aplica el mapeo por nombre de excepción de siempre.

| Código de error | Mensaje (ES) |
|---|---|
| `no_text_found` | No se encontró texto en el archivo |
| `image_decode_failed` | No se pudo leer la imagen (puede estar dañada) |
| `image_too_large` | La imagen es demasiado grande para procesarla |
| `ocr_engine_unavailable` | El motor de reconocimiento de texto no está disponible |
| `ocr_failed` | No se pudo reconocer el texto de la imagen |
| `pdf_open_failed` | No se pudo abrir el PDF (puede estar dañado) |
| `legacy_format` | Formato antiguo (.doc / .ppt) no soportado: guárdalo como .docx / .pptx e inténtalo de nuevo |
| `page_render_failed` | No se pudo procesar el documento (error al leer sus páginas) |
| `page_failed` | No se pudo procesar el documento |

Todo código nuevo necesita mensaje ES y EN (`tests/test_error_codes.py` lo comprueba). Las plantillas de avisos están en `WARNINGS` (`low_confidence_dropped`, `frames_skipped`, `page_failed`, `image_failed`, `image_failed_slide`, `images_skipped`); `issue_to_payload` usa `image_failed_slide` cuando el aviso trae diapositiva.

### 14.6 Dependencias

`requirements.txt` fija `markitdown[all]==0.1.6` (el OCR de Office depende de sus internos y su salida cambia entre versiones) y añade `rapidocr==3.10.0`, `opencv-python-headless>=4.9,<4.13`, `pypdfium2>=4.30` y `pdfminer.six` (explícitos aunque algunos lleguen transitivos).

### 14.7 Imágenes dentro de DOCX y PPTX (`ocr/office_images.py`)

> Introducido por el change `add-ocr-office-images`.

- **Ruta rápida:** sin imágenes incrustadas (`word/media/*`, `ppt/media/*`), o si el archivo no se puede abrir como zip/python-pptx, se delega en `convert_document` (salida idéntica a la de siempre; el motor OCR no se carga).
- **DOCX:** `pre_process_docx` (ecuaciones) → mammoth con `img_element` → cada imagen se sustituye en el HTML por sus párrafos de texto (o se quita) → `HtmlConverter`. El texto ocupa el lugar de la imagen; dentro de una celda de tabla va en una sola línea. Si la cadena propia falla antes de leer imágenes, se cae a `convert_document` (sin OCR) con una línea en stderr.
- **PPTX:** python-pptx abre el archivo y cada imagen (suelta, marcador con imagen o dentro de un grupo) se sustituye por un cuadro de texto en las mismas coordenadas con el alt text en cursiva y el texto OCR; la copia en memoria se convierte con markitdown (`converter.convert_stream`). El tipo de contenido sale de la parte del paquete.
- **Qué se lee** (calibrado con iconos y fotos reales y un PPTX real; ver el design del change):

| Constante | Valor | Significado |
|---|---|---|
| `OFFICE_MIN_AREA` | 0.01 | tamaño mostrado mínimo (fracción de la página o diapositiva); DOCX lo lee de `wp:extent` emparejado por SHA-1 y `w:pgSz` |
| `FALLBACK_MIN_SIDE_PX` / `FALLBACK_MIN_PIXELS` | 100 / 20 000 | respaldo en píxeles si no se conoce el tamaño mostrado (DOCX) |
| `OFFICE_MIN_TEXT_CHARS` | 6 | alfanuméricos mínimos para emitir el texto de una imagen (los iconos "leen" 1–5) |
| `SCAN_COVERAGE` | 0.5 | una imagen que se muestra a esta fracción o más se lee con reintento de orientación (`read_upright`); el resto con un único OCR (`read_simple`) |

- **Deduplicación:** cada imagen distinta (SHA-1) se lee una vez; el texto solo se emite en su primera aparición.
- **Alt text:** solo la descripción real (no el nombre de la forma, ni un nombre de archivo, ni "Imagen 3") y solo en imágenes relevantes o que aportan texto; se emite como línea en cursiva (`*texto*`) antes del texto OCR.
- **Avisos y errores:** `image_failed` por imagen (un único `try/except` por imagen, con log en stderr), `images_skipped` agregado para `image/x-emf`, `image/x-wmf` e `image/svg+xml`, `low_confidence_dropped` agregado solo si la imagen aporta texto. Sin motor OCR: error del archivo (`ocr_engine_unavailable`). Si no queda ningún texto: `no_text_found`.
- **Progreso y cancelación:** `file_progress` tras cada imagen (0–99) y `cancel_flag` antes de cada una; al cancelar devuelve `""`.
- **Salida distinta a la anterior (deliberada):** con imágenes desaparecen las líneas `![..](data:...)` y `![..](X.jpg)`.

