## ADDED Requirements

### Requirement: DropZone with react-dropzone
The system SHALL provide a `DropZone` using `useDropzone` with `noClick: true`, `multiple: true`, and MIME accept mapping from `SUPPORTED_EXTENSIONS`. File selection SHALL be via hidden input on button click.

#### Scenario: Files dropped
- **WHEN** user drops 3 PDFs
- **THEN** `onFilesAdded` SHALL be called with 3 File objects

#### Scenario: Drag active state
- **WHEN** a file is being dragged over the zone
- **THEN** border SHALL become solid accent, background SHALL change, icon SHALL scale to 1.1

### Requirement: DropZoneCompact for adding more files
The system SHALL provide a compact horizontal variant that is fully clickable (`noClick: false`), 40px tall, with only a Plus icon and "Add more files" text.

#### Scenario: Click to add files
- **WHEN** user clicks the compact dropzone
- **THEN** the native file picker SHALL open
