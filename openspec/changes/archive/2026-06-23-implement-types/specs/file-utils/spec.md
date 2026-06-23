## ADDED Requirements

### Requirement: getExtension function
The system SHALL provide a `getExtension(filename: string): string` function that extracts the file extension in lowercase without the leading dot.

#### Scenario: PDF with uppercase extension
- **WHEN** `getExtension("Mi Archivo.PDF")` is called
- **THEN** it SHALL return `"pdf"`

#### Scenario: MP3 with mixed case
- **WHEN** `getExtension("audio.MP3")` is called
- **THEN** it SHALL return `"mp3"`

#### Scenario: File without extension
- **WHEN** `getExtension("README")` is called
- **THEN** it SHALL return an empty string `""`

#### Scenario: File with multiple dots
- **WHEN** `getExtension("archive.tar.gz")` is called
- **THEN** it SHALL return `"gz"` (the last segment)

### Requirement: isSupportedExtension function
The system SHALL provide an `isSupportedExtension(ext: string): ext is SupportedExtension` type guard that checks if an extension is in `SUPPORTED_EXTENSIONS`.

#### Scenario: Supported extension
- **WHEN** `isSupportedExtension("pdf")` is called
- **THEN** it SHALL return `true` and narrow the type to `SupportedExtension`

#### Scenario: Unsupported extension
- **WHEN** `isSupportedExtension("zip")` is called
- **THEN** it SHALL return `false`

### Requirement: getFileCategory function
The system SHALL provide a `getFileCategory(ext: string): FileCategory | null` function that returns `'document'`, `'audio'`, or `null` based on the extension's presence in `DOCUMENT_EXTENSIONS` or `AUDIO_EXTENSIONS`.

#### Scenario: Document extension
- **WHEN** `getFileCategory("xlsx")` is called
- **THEN** it SHALL return `'document'`

#### Scenario: Audio extension
- **WHEN** `getFileCategory("mp3")` is called
- **THEN** it SHALL return `'audio'`

#### Scenario: Unsupported extension
- **WHEN** `getFileCategory("zip")` is called
- **THEN** it SHALL return `null`
