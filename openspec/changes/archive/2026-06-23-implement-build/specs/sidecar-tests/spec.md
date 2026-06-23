## ADDED Requirements

### Requirement: sanitizeFilename tests
The system SHALL provide parametrized pytest tests for `sanitize_filename()` with at least 9 cases covering accents, special chars, dots, empty stems.

#### Scenario: Accented filename
- **WHEN** `test_sanitize_filename("Mi Presentación 2024.pptx", "mi_presentacion_2024.md")` runs
- **THEN** it SHALL pass

### Requirement: write_message test
The system SHALL test that `write_message()` writes JSON + newline to stdout and calls flush.

#### Scenario: Write message format
- **WHEN** `write_message({"type": "test"})` is called
- **THEN** stdout SHALL contain `{"type": "test"}\n`

### Requirement: read_message test
The system SHALL test that `read_message()` correctly parses JSON from stdin.

#### Scenario: Read message
- **WHEN** stdin provides `'{"command": "convert"}\n'`
- **THEN** `read_message()` SHALL return `{"command": "convert"}`
