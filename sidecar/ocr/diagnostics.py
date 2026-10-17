# sidecar/ocr/diagnostics.py
"""
Errores y avisos de conversión con contexto trazable (archivo / página / etapa / código).
"""

import sys
from dataclasses import dataclass
from pathlib import Path

# Etapas: open | decode | classify | render | ocr | layout | assemble
# Códigos de error: ocr_engine_unavailable, ocr_failed, image_decode_failed, image_too_large, no_text_found
# Códigos solo de aviso: low_confidence_dropped, frames_skipped


class ConversionError(Exception):
    """Fallo de conversión de un archivo (o de una página que el llamador decide tratar como aviso)."""

    def __init__(self, code: str, stage: str, file: str | None = None, page: int | None = None,
                 cause: BaseException | None = None):
        self.code = code
        self.stage = stage
        self.file = Path(file).name if file else None  # solo el nombre: sin rutas completas en logs
        self.page = page
        self.cause = cause
        detail = f": {type(cause).__name__}: {cause}" if cause else ""
        super().__init__(f"{code} (file={self.file}, page={page}, stage={stage}){detail}")
        if cause is not None:
            self.__cause__ = cause


@dataclass(frozen=True)
class PageIssue:
    """Aviso no fatal. `count` se usa en avisos agregados (p. ej. líneas descartadas)."""
    code: str
    stage: str
    page: int | None = None
    count: int | None = None


def log_issue(issue: PageIssue, file: str, error: BaseException | None = None) -> None:
    """Una línea en stderr por incidente. Sin contenido del documento ni rutas completas."""
    detail = f" err={type(error).__name__}: {error}" if error else ""
    print(
        f"[Sidecar][ocr] file={Path(file).name} page={issue.page} stage={issue.stage} "
        f"code={issue.code} count={issue.count}{detail}",
        file=sys.stderr,
    )
