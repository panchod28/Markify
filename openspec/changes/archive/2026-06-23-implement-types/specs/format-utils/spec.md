## ADDED Requirements

### Requirement: formatFileSize function
The system SHALL provide a `formatFileSize(bytes: number): string` function that converts bytes to a human-readable string with one decimal place using binary units (1024).

#### Scenario: Zero bytes
- **WHEN** `formatFileSize(0)` is called
- **THEN** it SHALL return `"0 B"`

#### Scenario: Less than 1 KB
- **WHEN** `formatFileSize(1023)` is called
- **THEN** it SHALL return `"1023 B"`

#### Scenario: Exactly 1 KB
- **WHEN** `formatFileSize(1024)` is called
- **THEN** it SHALL return `"1.0 KB"`

#### Scenario: Fractional KB
- **WHEN** `formatFileSize(1536)` is called
- **THEN** it SHALL return `"1.5 KB"`

#### Scenario: Exactly 1 MB
- **WHEN** `formatFileSize(1048576)` is called
- **THEN** it SHALL return `"1.0 MB"`

#### Scenario: Exactly 1 GB
- **WHEN** `formatFileSize(1073741824)` is called
- **THEN** it SHALL return `"1.0 GB"`

### Requirement: generateZipName function
The system SHALL provide a `generateZipName(): string` function that generates a suggested ZIP filename with the current date and time in the format `"conversion_YYYY-MM-DD_HH-MM.zip"`.

#### Scenario: ZIP name generation
- **WHEN** `generateZipName()` is called on 2026-06-22 at 14:30
- **THEN** it SHALL return `"conversion_2026-06-22_14-30.zip"`

#### Scenario: ZIP name uses colons replaced by hyphens
- **WHEN** `generateZipName()` is called
- **THEN** the time portion SHALL use hyphens instead of colons (Windows-compatible)
