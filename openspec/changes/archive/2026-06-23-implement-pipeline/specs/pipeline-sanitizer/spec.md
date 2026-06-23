## ADDED Requirements

### Requirement: 10-step sanitization algorithm in TypeScript
The system SHALL provide `sanitizeFilename()` in `src/lib/sanitizer.ts` that follows the exact 10-step algorithm: extract stem → NFKD normalize → strip combining chars → lowercase → replace spaces/dashes/dots with `_` → remove non-alphanumeric → collapse `_` → trim `_` → fallback `'archivo_sin_nombre'` → append `.md`.

#### Scenario: PowerPoint with spaces and accents
- **WHEN** `sanitizeFilename("Mi Presentación 2024.pptx")` is called
- **THEN** it SHALL return `"mi_presentacion_2024.md"`

#### Scenario: File with dots inside name
- **WHEN** `sanitizeFilename("file.with.dots.inside.pdf")` is called
- **THEN** it SHALL return `"file_with_dots_inside.md"`

#### Scenario: Only special characters
- **WHEN** `sanitizeFilename("!@#$%.xlsx")` is called
- **THEN** it SHALL return `"archivo_sin_nombre.md"`

#### Scenario: Umlaut and special chars
- **WHEN** `sanitizeFilename("über die Straße.pdf")` is called
- **THEN** it SHALL return `"uber_die_strae.md"`
