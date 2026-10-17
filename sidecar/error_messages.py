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
        # Códigos de ConversionError (OCR)
        "no_text_found":          "No se encontró texto en el archivo",
        "image_decode_failed":    "No se pudo leer la imagen (puede estar dañada)",
        "image_too_large":        "La imagen es demasiado grande para procesarla",
        "ocr_engine_unavailable": "El motor de reconocimiento de texto no está disponible",
        "ocr_failed":             "No se pudo reconocer el texto de la imagen",
        "pdf_open_failed":        "No se pudo abrir el PDF (puede estar dañado)",
        "page_render_failed":     "No se pudo procesar el documento (error al leer sus páginas)",
        "page_failed":            "No se pudo procesar el documento",
    },
    "en": {
        "FileNotFoundError":  "Could not find the file",
        "PermissionError":    "The file is password protected",
        "file_corrupted":     "Could not read the file (it may be corrupted)",
        "ValueError_empty":   "No text was found in the file",
        "audio_too_short":    "The audio is too short or contains no detected speech",
        "ConnectionError":    "No internet connection. Check your connection and try again.",
        "unknown":            "Unexpected error while converting the file",
        # ConversionError codes (OCR)
        "no_text_found":          "No text was found in the file",
        "image_decode_failed":    "Could not read the image (it may be corrupted)",
        "image_too_large":        "The image is too large to process",
        "ocr_engine_unavailable": "The text recognition engine is not available",
        "ocr_failed":             "Could not recognize the text in the image",
        "pdf_open_failed":        "Could not open the PDF (it may be corrupted)",
        "page_render_failed":     "Could not process the document (error reading its pages)",
        "page_failed":            "Could not process the document",
    }
}

# Avisos no fatales (PageIssue.code). {count} / {page} se rellenan en issue_to_payload.
WARNINGS = {
    "es": {
        "low_confidence_dropped": "Se omitieron {count} líneas con baja confianza de lectura",
        "frames_skipped":         "Solo se procesó el primer fotograma ({count} omitidos)",
        "page_failed":            "La página {page} no se pudo procesar",
    },
    "en": {
        "low_confidence_dropped": "{count} low-confidence lines were left out",
        "frames_skipped":         "Only the first frame was processed ({count} skipped)",
        "page_failed":            "Page {page} could not be processed",
    },
}


def issue_to_payload(issue, lang: str = "en") -> dict:
    """PageIssue -> elemento de `warnings` del file_result: {page, stage, code, message}."""
    templates = WARNINGS.get(lang, WARNINGS["en"])
    template = templates.get(issue.code, issue.code)
    return {
        "page": issue.page,
        "stage": issue.stage,
        "code": issue.code,
        "message": template.format(count=issue.count, page=issue.page),
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

    # ConversionError trae un código estable: tiene prioridad sobre el mapeo por nombre de excepción.
    code = getattr(exception, "code", None)
    if code in msgs:
        return msgs[code]

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
