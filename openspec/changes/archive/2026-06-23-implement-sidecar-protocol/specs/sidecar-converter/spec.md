## ADDED Requirements

### Requirement: MarkItDown singleton instance
The system SHALL instantiate `MarkItDown()` once as a module-level variable for reuse across conversions.

#### Scenario: Multiple conversions
- **WHEN** 3 documents are converted sequentially
- **THEN** the same `MarkItDown` instance SHALL be reused

### Requirement: File existence and size validation
The system SHALL verify the file exists and is not empty before attempting conversion. It SHALL raise `FileNotFoundError` or `ValueError` accordingly.

#### Scenario: File does not exist
- **WHEN** `convert_document("/nonexistent.pdf")` is called
- **THEN** `FileNotFoundError` SHALL be raised

#### Scenario: Empty file
- **WHEN** `convert_document("/empty.pdf")` is called on a 0-byte file
- **THEN** `ValueError` with message "El archivo está vacío" SHALL be raised

### Requirement: Password-protected file detection
The system SHALL detect password-protected files and raise `PermissionError`.

#### Scenario: Password-protected PDF
- **WHEN** markitdown raises a password-related error
- **THEN** `PermissionError` SHALL be raised

### Requirement: Corrupted file detection
The system SHALL detect corrupted files and raise `RuntimeError("file_corrupted")`.

#### Scenario: Corrupted DOCX
- **WHEN** markitdown raises a corruption-related error
- **THEN** `RuntimeError("file_corrupted")` SHALL be raised

### Requirement: Empty content detection
The system SHALL verify the extracted text is not empty or whitespace-only.

#### Scenario: File with no extractable text
- **WHEN** markitdown returns empty content
- **THEN** `ValueError("No se encontró texto en el archivo")` SHALL be raised
