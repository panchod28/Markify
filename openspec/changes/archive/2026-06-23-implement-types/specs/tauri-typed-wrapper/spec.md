## ADDED Requirements

### Requirement: tauriCommands typed wrapper
The system SHALL provide a `tauriCommands` object with typed `invoke` wrappers for all backend commands: `startConversion`, `cancelConversion`, `saveMarkdown`, `saveZip`, `openInFolder`, `checkWhisperModel`, `downloadWhisperModel`, `getAppVersion`.

#### Scenario: startConversion with typed payload
- **WHEN** `tauriCommands.startConversion(payload)` is called with a valid `StartConversionPayload`
- **THEN** it SHALL invoke `'start_conversion'` with the typed payload via `@tauri-apps/api/core`

#### Scenario: cancelConversion
- **WHEN** `tauriCommands.cancelConversion()` is called
- **THEN** it SHALL invoke `'cancel_conversion'` with no arguments

#### Scenario: saveMarkdown with content
- **WHEN** `tauriCommands.saveMarkdown(markdownContent, suggestedName)` is called
- **THEN** it SHALL invoke `'save_markdown'` with `{ content, suggestedName }` and return `Promise<string | null>`

#### Scenario: saveZip with typed payload
- **WHEN** `tauriCommands.saveZip(payload)` is called with a valid `SaveZipPayload`
- **THEN** it SHALL invoke `'save_zip'` with the typed payload and return `Promise<string | null>`

#### Scenario: getAppVersion
- **WHEN** `tauriCommands.getAppVersion()` is called
- **THEN** it SHALL invoke `'get_app_version'` and return `Promise<string>`

### Requirement: tauriEvents typed listener wrappers
The system SHALL provide a `tauriEvents` object with typed `listen` wrappers for all backend-to-frontend events: `onFileUpdate`, `onModelDownloadProgress`, `onModelDownloadComplete`, `onModelDownloadError`, `onConversionComplete`, `onConversionCancelled`.

#### Scenario: Listening to file update events
- **WHEN** `tauriEvents.onFileUpdate(handler)` is registered
- **THEN** the handler SHALL receive a `ConversionProgressEvent` type and the function SHALL return `Promise<UnlistenFn>`

#### Scenario: Listening to model download progress
- **WHEN** `tauriEvents.onModelDownloadProgress(handler)` is registered
- **THEN** the handler SHALL receive a `ModelDownloadProgressEvent` type

#### Scenario: Listening to conversion complete
- **WHEN** `tauriEvents.onConversionComplete(handler)` is registered
- **THEN** the handler SHALL be called with no arguments when conversion finishes

#### Scenario: Listening to conversion cancelled
- **WHEN** `tauriEvents.onConversionCancelled(handler)` is registered
- **THEN** the handler SHALL be called with no arguments when conversion is cancelled

### Requirement: Import path convention
The system SHALL import types using `import type { ... } from '@/types'` pattern throughout the project, and `invoke`/`listen` from `'@tauri-apps/api/core'` and `'@tauri-apps/api/event'` respectively.

#### Scenario: Type-only import
- **WHEN** a component needs `ConversionFile` type
- **THEN** it SHALL use `import type { ConversionFile } from '@/types'`
