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
