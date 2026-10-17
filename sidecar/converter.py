# sidecar/converter.py
"""
Conversión de documentos a Markdown usando markitdown.
"""

from pathlib import Path
from markitdown import MarkItDown

from ocr.diagnostics import ConversionError


_md_converter = MarkItDown()

# Binarios antiguos de Office: markitdown no los soporta (el frontend ya los rechaza antes de llegar aquí).
LEGACY_SUFFIXES = (".doc", ".ppt")


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

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    if path.suffix.lower() in LEGACY_SUFFIXES:
        raise ConversionError("legacy_format", "open", path.name)

    if path.stat().st_size == 0:
        raise ValueError("El archivo está vacío")

    try:
        result = _md_converter.convert(file_path)
        content = result.text_content

        if not content or not content.strip():
            raise ValueError("No se encontró texto en el archivo")

        return content

    except PermissionError:
        raise PermissionError("Archivo protegido con contraseña")

    except (FileNotFoundError, ValueError, PermissionError):
        raise

    except Exception as e:
        error_str = str(e).lower()
        if "password" in error_str or "encrypted" in error_str:
            raise PermissionError("Archivo protegido con contraseña")
        if "corrupt" in error_str or "invalid" in error_str:
            raise RuntimeError("file_corrupted")
        raise RuntimeError(f"unknown: {e}")


def convert_stream(stream, extension: str) -> str:
    """Igual que convert_document pero desde un flujo en memoria (copia de un PPTX con las imágenes ya leídas)."""
    content = _md_converter.convert_stream(stream, file_extension=extension).text_content
    if not content or not content.strip():
        raise ValueError("No se encontró texto en el archivo")
    return content
