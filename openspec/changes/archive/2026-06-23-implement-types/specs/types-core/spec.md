## ADDED Requirements

### Requirement: FileCategory union type
The system SHALL provide a `FileCategory` type with values `'document'` and `'audio'` to determine which sidecar tool processes a file.

#### Scenario: Categorizing a PDF
- **WHEN** a file with extension `.pdf` is added
- **THEN** its category SHALL be `'document'`

#### Scenario: Categorizing an MP3
- **WHEN** a file with extension `.mp3` is added
- **THEN** its category SHALL be `'audio'`

### Requirement: FileStatus union type
The system SHALL provide a `FileStatus` type with values `'pending'`, `'processing'`, `'completed'`, and `'error'` to track conversion state of each file.

#### Scenario: Initial file state
- **WHEN** a new `ConversionFile` is created
- **THEN** its status SHALL be `'pending'`

#### Scenario: Conversion completed
- **WHEN** the sidecar finishes processing a file successfully
- **THEN** its status SHALL be `'completed'`

### Requirement: AppState union type
The system SHALL provide an `AppState` type with values `'empty'`, `'files-ready'`, `'processing'`, and `'results'` to control which view `App.tsx` renders.

#### Scenario: App starts with no files
- **WHEN** the application launches for the first time
- **THEN** the appState SHALL be `'empty'`

#### Scenario: Files added but not converted
- **WHEN** one or more files are added to the queue
- **THEN** the appState SHALL transition to `'files-ready'`

### Requirement: Theme and Language types
The system SHALL provide `Theme` (`'light' | 'dark' | 'system'`), `ResolvedTheme` (`'light' | 'dark'`), `Language` (`'en' | 'es' | 'system'`), and `ResolvedLanguage` (`'en' | 'es'`) types.

#### Scenario: System theme detection
- **WHEN** the user sets theme to `'system'`
- **THEN** the `ResolvedTheme` SHALL be determined by `prefers-color-scheme` media query

#### Scenario: System language detection
- **WHEN** the user sets language to `'system'`
- **THEN** the `ResolvedLanguage` SHALL be determined by `navigator.language`

### Requirement: PreviewViewMode type
The system SHALL provide a `PreviewViewMode` type with values `'rendered'` and `'raw'` to control markdown preview display.

#### Scenario: Rendered mode
- **WHEN** preview mode is `'rendered'`
- **THEN** the preview panel SHALL render markdown using ReactMarkdown

#### Scenario: Raw mode
- **WHEN** preview mode is `'raw'`
- **THEN** the preview panel SHALL display raw markdown in a `<pre><code>` block

### Requirement: ConversionFile interface
The system SHALL provide a `ConversionFile` interface with all fields defined in spec 01: `id`, `originalName`, `sanitizedName`, `path`, `sizeBytes`, `formattedSize`, `category`, `extension`, `status`, `progress`, optional `errorMessage`, and optional `markdownContent`.

#### Scenario: File created with all required fields
- **WHEN** a file is added via the dropzone or file picker
- **THEN** a `ConversionFile` object SHALL be created with a UUID v4 `id`, computed `category`, computed `extension`, `status` of `'pending'`, and `progress` of `0`

#### Scenario: File in error state
- **WHEN** a file fails conversion
- **THEN** its `status` SHALL be `'error'` and `errorMessage` SHALL contain a user-facing error string

#### Scenario: File completed successfully
- **WHEN** a file completes conversion
- **THEN** its `status` SHALL be `'completed'` and `markdownContent` SHALL contain the markdown output

### Requirement: ConversionProgressEvent interface
The system SHALL provide a `ConversionProgressEvent` interface matching the payload of `conversion:file-update` Tauri event: `fileId`, `status`, `progress`, optional `errorMessage`, optional `markdownContent`.

#### Scenario: Progress event received
- **WHEN** the sidecar emits a progress update for a file
- **THEN** the event SHALL contain the `fileId` matching the `ConversionFile.id`

### Requirement: ModelDownloadProgressEvent interface
The system SHALL provide a `ModelDownloadProgressEvent` interface with `percent`, `downloadedMB`, and `totalMB` fields for the `model:download-progress` event.

#### Scenario: Download progress update
- **WHEN** the Whisper model is being downloaded
- **THEN** progress events SHALL be emitted with `percent` between 0 and 100

### Requirement: ConversionSummary interface
The system SHALL provide a `ConversionSummary` interface with computed fields `total`, `completed`, `failed`, and `pending` derived from the store's file array.

#### Scenario: Summary after partial conversion
- **WHEN** 5 files are in the store (2 completed, 1 failed, 2 pending)
- **THEN** the summary SHALL show `total: 5`, `completed: 2`, `failed: 1`, `pending: 2`

### Requirement: StartConversionPayload interface
The system SHALL provide a `StartConversionPayload` interface with `files` (array of `{id, path, category}`) and `lang` (ResolvedLanguage).

#### Scenario: Starting a batch conversion
- **WHEN** the user clicks "Convert"
- **THEN** a payload SHALL be constructed with all files and the resolved language

### Requirement: SaveZipPayload interface
The system SHALL provide a `SaveZipPayload` interface with `files` (array of `{name, content}`) and `suggestedName` (string).

#### Scenario: Exporting results as ZIP
- **WHEN** the user clicks "Save ZIP"
- **THEN** a payload SHALL be constructed with all completed files and a generated ZIP name

### Requirement: Document extension constants
The system SHALL define `DOCUMENT_EXTENSIONS` as a `const` array containing: `'pdf'`, `'pptx'`, `'ppt'`, `'xlsx'`, `'xls'`, `'docx'`, `'doc'`, `'html'`, `'csv'` and derive `DocumentExtension` type from it.

#### Scenario: Valid document extension
- **WHEN** a file has extension `'pptx'`
- **THEN** it SHALL be recognized as a document extension

#### Scenario: Invalid extension
- **WHEN** a file has extension `'zip'`
- **THEN** it SHALL NOT be recognized as a document extension

### Requirement: Audio extension constants
The system SHALL define `AUDIO_EXTENSIONS` as a `const` array containing: `'mp3'`, `'mp4'`, `'wav'`, `'m4a'`, `'ogg'`, `'webm'`, `'flac'`, `'aac'` and derive `AudioExtension` type from it.

#### Scenario: Valid audio extension
- **WHEN** a file has extension `'wav'`
- **THEN** it SHALL be recognized as an audio extension

### Requirement: Supported extension union
The system SHALL define `SUPPORTED_EXTENSIONS` as the spread of `DOCUMENT_EXTENSIONS` and `AUDIO_EXTENSIONS` and derive `SupportedExtension` type from it.

#### Scenario: All supported extensions
- **WHEN** querying supported extensions
- **THEN** the union SHALL contain all 17 extensions from both arrays

### Requirement: Configuration constants
The system SHALL define the following constants: `MAX_FILE_SIZE_BYTES` (500 MB), `MAX_TOTAL_BATCH_SIZE_BYTES` (2 GB), `MAX_FILES_PER_BATCH` (50), `WHISPER_MODEL_NAME` (`'base'`), `WHISPER_MODEL_SIZE_MB` (145), `WINDOW_DEFAULT_WIDTH` (960), `WINDOW_DEFAULT_HEIGHT` (680), `WINDOW_MIN_WIDTH` (800), `WINDOW_MIN_HEIGHT` (600).

#### Scenario: File size validation
- **WHEN** a file larger than 500 MB is added
- **THEN** it SHALL be rejected based on `MAX_FILE_SIZE_BYTES`

#### Scenario: Batch size validation
- **WHEN** 51 files are added
- **THEN** the 51st file SHALL be rejected based on `MAX_FILES_PER_BATCH`

### Requirement: FILE_ICON_MAP constant
The system SHALL provide a `FILE_ICON_MAP` record mapping each `SupportedExtension` to an object with `icon` (lucide-react icon name) and `colorClass` (Tailwind CSS class).

#### Scenario: Icon lookup for PDF
- **WHEN** looking up the icon for extension `'pdf'`
- **THEN** the map SHALL return `{ icon: 'FileText', colorClass: 'text-red-500' }`

#### Scenario: Icon lookup for MP4
- **WHEN** looking up the icon for extension `'mp4'`
- **THEN** the map SHALL return `{ icon: 'Video', colorClass: 'text-indigo-500' }`
