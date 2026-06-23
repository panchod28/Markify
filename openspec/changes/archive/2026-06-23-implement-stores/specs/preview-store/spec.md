## ADDED Requirements

### Requirement: PreviewStore interface
The system SHALL provide a `PreviewStore` with `selectedFileId` (nullable string), `viewMode` (PreviewViewMode), and actions `selectFile`, `toggleViewMode`, `reset`.

#### Scenario: Initial state
- **WHEN** the preview store is created
- **THEN** `selectedFileId` SHALL be `null` and `viewMode` SHALL be `'rendered'`

### Requirement: selectFile action
The system SHALL update `selectedFileId` when `selectFile(id)` is called.

#### Scenario: Select a file
- **WHEN** `selectFile('abc-123')` is called
- **THEN** `selectedFileId` SHALL be `'abc-123'`

### Requirement: toggleViewMode action
The system SHALL toggle `viewMode` between `'rendered'` and `'raw'` when `toggleViewMode()` is called.

#### Scenario: Toggle from rendered to raw
- **WHEN** `viewMode` is `'rendered'` and `toggleViewMode()` is called
- **THEN** `viewMode` SHALL become `'raw'`

#### Scenario: Toggle from raw to rendered
- **WHEN** `viewMode` is `'raw'` and `toggleViewMode()` is called
- **THEN** `viewMode` SHALL become `'rendered'`

### Requirement: reset action
The system SHALL reset `selectedFileId` to `null` and `viewMode` to `'rendered'` when `reset()` is called.

#### Scenario: Start new conversion
- **WHEN** `reset()` is called
- **THEN** `selectedFileId` SHALL be `null` and `viewMode` SHALL be `'rendered'`
