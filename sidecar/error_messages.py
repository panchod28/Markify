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
