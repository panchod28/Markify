## ADDED Requirements

### Requirement: useTauriEvents hook registration
The system SHALL provide a `useTauriEvents()` hook that registers all Tauri event listeners on mount and cleans them up on unmount.

#### Scenario: Hook mounted in App.tsx
- **WHEN** `useTauriEvents()` is called in `App` component
- **THEN** all 6 event listeners SHALL be registered with `tauriEvents.*`

### Requirement: Event dispatch to store
The system SHALL dispatch Tauri events to `useConversionStore.getState()` internal handlers without creating React subscriptions.

#### Scenario: File update event received
- **WHEN** a `conversion:file-update` event arrives
- **THEN** `useConversionStore.getState()._handleFileUpdate(event)` SHALL be called

#### Scenario: Download complete event received
- **WHEN** a `model:download-complete` event arrives
- **THEN** `useConversionStore.getState()._handleModelDownloadComplete()` SHALL be called

### Requirement: Error logging for model download
The system SHALL reset download state and log to console when a `model:download-error` event is received.

#### Scenario: Model download fails
- **WHEN** a `model:download-error` event arrives with message "Network error"
- **THEN** `whisperModelDownloading` SHALL be `false`, progress SHALL be `0`, and the error SHALL be logged

### Requirement: Cleanup on unmount
The system SHALL unregister all listeners when the hook unmounts.

#### Scenario: App unmounts
- **WHEN** the component using `useTauriEvents` is removed
- **THEN** all registered `UnlistenFn` callbacks SHALL be invoked to prevent memory leaks
