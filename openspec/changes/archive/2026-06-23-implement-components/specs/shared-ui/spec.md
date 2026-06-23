## ADDED Requirements

### Requirement: FileIcon from FILE_ICON_MAP
The system SHALL render the Lucide icon corresponding to a file extension using `FILE_ICON_MAP`. Unknown extensions SHALL use `FileText` with `text-gray-400`.

#### Scenario: PDF icon
- **WHEN** `extension === 'pdf'`
- **THEN** `FileText` icon with `text-red-500` SHALL be rendered

### Requirement: WhisperModelModal with 3 phases
The system SHALL show a dialog for model download with: (1) confirmation with buttons, (2) progress bar during download with no close allowed, (3) error with retry option.

#### Scenario: Download in progress
- **WHEN** `isDownloading` is true
- **THEN** the dialog SHALL show progress bar and SHALL NOT close on Escape or click outside

### Requirement: ConfirmDialog reusable
The system SHALL provide a confirmation dialog with title, description, confirm/dismiss labels, and optional destructive variant.

#### Scenario: Destructive confirmation
- **WHEN** `variant === 'destructive'`
- **THEN** the confirm button SHALL use error/destructive styling

### Requirement: ValidationErrorToast auto-dismiss
The system SHALL show up to 3 validation errors in a toast (bottom-right) that auto-dismisses after 5 seconds, with "and X more..." for overflow.

#### Scenario: 5 errors
- **WHEN** `errors.length === 5`
- **THEN** the toast SHALL show 3 errors + "y 2 más..."

### Requirement: App.tsx state router
The system SHALL render one view at a time based on `appState`, using `AnimatePresence mode="wait"` with fade transitions, plus modals always mounted.

#### Scenario: Transition to processing
- **WHEN** `appState` changes from `'files-ready'` to `'processing'`
- **THEN** FileList SHALL fade out and ProcessingView SHALL fade in
