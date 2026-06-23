## ADDED Requirements

### Requirement: File validation errors discriminated union
The system SHALL define a `FileValidationError` discriminated union with types: `unsupported`, `too_large`, `batch_too_large`, `too_many_files`, `duplicate`.

#### Scenario: Unsupported extension
- **WHEN** a file with extension `.zip` is added
- **THEN** an error of type `unsupported` SHALL be generated with the filename and extension

#### Scenario: File too large
- **WHEN** a file larger than `MAX_FILE_SIZE_BYTES` is added
- **THEN** an error of type `too_large` SHALL be generated with the filename and size

### Requirement: appState machine
The system SHALL manage `appState` as a state machine with transitions: `empty` ↔ `files-ready` ↔ `processing` → `results` → `empty`.

#### Scenario: Add files transitions to files-ready
- **WHEN** valid files are added via `addFiles()` and `appState` is `empty`
- **THEN** `appState` SHALL transition to `files-ready`

#### Scenario: Start conversion transitions to processing
- **WHEN** `startConversion()` is called and `appState` is `files-ready`
- **THEN** `appState` SHALL transition to `processing`

#### Scenario: Conversion complete transitions to results
- **WHEN** the backend emits `conversion:complete`
- **THEN** `appState` SHALL transition to `results`

#### Scenario: Cancel returns to files-ready
- **WHEN** `cancelConversion()` completes
- **THEN** `appState` SHALL transition to `files-ready`

#### Scenario: Reset always returns to empty
- **WHEN** `resetToEmpty()` is called from any state
- **THEN** `appState` SHALL be `empty`

### Requirement: addFiles validation
The system SHALL validate files on `addFiles()` checking: supported extension, max file size, max batch size, max file count, and duplicates. Errors SHALL be collected in `validationErrors[]` without throwing.

#### Scenario: Mixed valid and invalid files
- **WHEN** 3 files are added (2 valid PDFs, 1 zip)
- **THEN** the 2 PDFs SHALL be added to `files` and 1 `unsupported` error SHALL be in `validationErrors`

#### Scenario: Batch size limit exceeded
- **WHEN** adding a file would exceed `MAX_TOTAL_BATCH_SIZE_BYTES`
- **THEN** a `batch_too_large` error SHALL be generated and remaining files SHALL NOT be processed

#### Scenario: Too many files
- **WHEN** adding files would exceed `MAX_FILES_PER_BATCH`
- **THEN** a `too_many_files` error SHALL be generated and NO files SHALL be added

### Requirement: Conversion file creation
The system SHALL create `ConversionFile` objects on `addFiles()` with UUID `id`, computed `sanitizedName`, `formattedSize`, `category`, `extension`, initial `status: 'pending'`, and `progress: 0`.

#### Scenario: PDF file created
- **WHEN** a PDF file `My Doc.pdf` is added
- **THEN** a `ConversionFile` SHALL be created with `category: 'document'`, `extension: 'pdf'`, `status: 'pending'`

### Requirement: Getters for computed state
The system SHALL provide getters: `summary`, `hasAudioFiles`, `completedFiles`, `failedFiles`, `pendingFiles`, `allCompleted`, `totalBatchSizeBytes`.

#### Scenario: Summary after mixed results
- **WHEN** 5 files exist (2 completed, 1 error, 2 pending)
- **THEN** `summary` SHALL be `{ total: 5, completed: 2, failed: 1, pending: 2 }`

#### Scenario: All completed check
- **WHEN** all files have status `completed` or `error`
- **THEN** `allCompleted` SHALL be `true`

### Requirement: startConversion resets file state
The system SHALL reset all files to `status: 'pending'`, `progress: 0`, clear `errorMessage` and `markdownContent` before starting conversion.

#### Scenario: Retry after partial conversion
- **WHEN** `startConversion()` is called after a previous conversion
- **THEN** all files SHALL have `status: 'pending'` and `progress: 0`

### Requirement: cancelConversion with isCancelling flag
The system SHALL set `isCancelling: true` before invoking `cancel_conversion` to show UI feedback.

#### Scenario: Cancel in progress
- **WHEN** user clicks Cancel and `cancelConversion()` is called
- **THEN** `isCancelling` SHALL be `true` and the cancel button SHALL show a loading state

### Requirement: retryFailed only processes error files
The system SHALL only retry files with `status: 'error'` when `retryFailed()` is called, leaving completed files untouched.

#### Scenario: Retry after 2 failures
- **WHEN** 3 files exist (1 completed, 2 errors) and `retryFailed()` is called
- **THEN** only the 2 error files SHALL be reset to `pending` and sent to the backend

### Requirement: Whisper model management
The system SHALL provide `checkWhisperModel()` and `startModelDownload()` actions that invoke corresponding Tauri commands and update state.

#### Scenario: Check model available
- **WHEN** `checkWhisperModel()` is called and the model is present
- **THEN** `whisperModelAvailable` SHALL be `true`

#### Scenario: Download progress
- **WHEN** `startModelDownload()` is called
- **THEN** `whisperModelDownloading` SHALL be `true` and `whisperModelDownloadProgress` SHALL reset to `0`

### Requirement: Internal event handlers
The system SHALL provide prefixed `_handleFileUpdate`, `_handleModelDownloadProgress`, `_handleModelDownloadComplete`, `_handleConversionComplete`, `_handleConversionCancelled` actions called only from `useTauriEvents`.

#### Scenario: File update event
- **WHEN** `_handleFileUpdate({ fileId: 'abc', status: 'completed', progress: 100, markdownContent: '...' })` is called
- **THEN** the file with id `'abc'` SHALL have `status: 'completed'`, `progress: 100`, and `markdownContent` set
