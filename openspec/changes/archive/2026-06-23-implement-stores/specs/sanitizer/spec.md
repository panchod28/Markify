## ADDED Requirements

### Requirement: sanitizeFilename function
The system SHALL provide a `sanitizeFilename(filename: string): string` function that converts a raw filename into a safe markdown filename. It SHALL replace extension with `.md`, transliterate accented characters, replace whitespace with underscores, and remove unsafe characters.

#### Scenario: PowerPoint file with spaces and accents
- **WHEN** `sanitizeFilename("Mi Presentación 2024.pptx")` is called
- **THEN** it SHALL return `"mi_presentacion_2024.md"`

#### Scenario: PDF with uppercase
- **WHEN** `sanitizeFilename("REPORT.PDF")` is called
- **THEN** it SHALL return `"report.md"`

#### Scenario: Audio file
- **WHEN** `sanitizeFilename("Grabación.mp3")` is called
- **THEN** it SHALL return `"grabacion.md"`

#### Scenario: File with special characters
- **WHEN** `sanitizeFilename("doc #1 (final).docx")` is called
- **THEN** special characters SHALL be removed and the result SHALL end with `.md`

### Requirement: Sanitization to lowercase with underscores
The system SHALL convert the sanitized name to lowercase and replace sequences of whitespace/dashes with single underscores.

#### Scenario: Multiple spaces
- **WHEN** `sanitizeFilename("My   Big   File.pdf")` is called
- **THEN** it SHALL return `"my_big_file.md"`
