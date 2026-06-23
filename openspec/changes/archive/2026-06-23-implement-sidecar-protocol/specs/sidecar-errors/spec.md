## ADDED Requirements

### Requirement: Bilingual error messages
The system SHALL provide error messages in Spanish and English keyed by exception type.

#### Scenario: Spanish error for file not found
- **WHEN** `get_error_message(FileNotFoundError(), "es")` is called
- **THEN** it SHALL return `"No se pudo encontrar el archivo"`

#### Scenario: English error for password protected
- **WHEN** `get_error_message(PermissionError(), "en")` is called
- **THEN** it SHALL return `"The file is password protected"`

### Requirement: Default language fallback
The system SHALL fall back to English if the requested language is not available.

#### Scenario: Unsupported language
- **WHEN** `get_error_message(err, "fr")` is called
- **THEN** English messages SHALL be used

### Requirement: Exception type-based routing
The system SHALL route exceptions by type: `FileNotFoundError`, `PermissionError`, `ConnectionError`, `ValueError` (with sub-routing for `audio_too_short`), `RuntimeError` (with sub-routing for `file_corrupted`), and a generic fallback.

#### Scenario: RuntimeError with file_corrupted
- **WHEN** `get_error_message(RuntimeError("file_corrupted"), "es")` is called
- **THEN** it SHALL return `"No se pudo leer el archivo (puede estar dañado)"`

#### Scenario: Unknown exception
- **WHEN** `get_error_message(SomeUnknownException(), "es")` is called
- **THEN** it SHALL return `"Error inesperado al convertir el archivo"`
