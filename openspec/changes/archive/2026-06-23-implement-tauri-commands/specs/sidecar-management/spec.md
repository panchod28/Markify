## ADDED Requirements

### Requirement: spawn_sidecar function
The system SHALL provide a `spawn_sidecar` function that spawns the `markify-sidecar` process, stores the child handle, and starts a background loop reading stdout lines.

#### Scenario: Sidecar spawned on app start
- **WHEN** the Tauri app `setup()` hook runs
- **THEN** the sidecar process SHALL be spawned and stdout reading SHALL begin

#### Scenario: Sidecar not found
- **WHEN** the sidecar binary is missing from `binaries/`
- **THEN** `app.shell().sidecar()` SHALL return an error and the app SHALL NOT crash

### Requirement: Stdout line processing loop
The system SHALL spawn an async task using `tauri::async_runtime::spawn` that reads `CommandEvent` from the sidecar receiver and processes `Stdout`, `Stderr`, `Error`, and `Terminated` events.

#### Scenario: Stdout line received
- **WHEN** the sidecar writes a JSON line to stdout
- **THEN** `handle_sidecar_output` SHALL be called with the app handle and the line bytes

#### Scenario: Stderr line received
- **WHEN** the sidecar writes to stderr
- **THEN** the content SHALL be logged with `[Sidecar stderr]` prefix

#### Scenario: Sidecar terminates
- **WHEN** the sidecar process exits
- **THEN** the loop SHALL break and log the exit status

### Requirement: handle_sidecar_output message router
The system SHALL parse each stdout line as JSON and route messages by `type` field: `file_progress`/`file_result` → `conversion:file-update`, `conversion_complete` → `conversion:complete`, `conversion_cancelled` → `conversion:cancelled`, `model_progress` → `model:download-progress`, `model_ready` → `model:download-complete`, `model_error` → `model:download-error`.

#### Scenario: File progress event
- **WHEN** sidecar stdout contains `{ "type": "file_progress", "payload": { "fileId": "abc", "progress": 50 } }`
- **THEN** a `conversion:file-update` Tauri event SHALL be emitted with the payload

#### Scenario: Invalid JSON
- **WHEN** sidecar stdout contains non-JSON text
- **THEN** an error SHALL be logged and the message SHALL be ignored

### Requirement: check_whisper_model command
The system SHALL provide a `check_whisper_model` command that sends `{ "command": "check_model" }` to the sidecar and awaits a `model_status` reply via oneshot channel with 5-second timeout.

#### Scenario: Model is present
- **WHEN** the sidecar replies with `{ "type": "model_status", "payload": { "available": true } }`
- **THEN** the command SHALL return `Ok(true)`

#### Scenario: Model not found
- **WHEN** the sidecar replies with `{ "available": false }`
- **THEN** the command SHALL return `Ok(false)`

#### Scenario: Sidecar does not respond
- **WHEN** the sidecar fails to reply within 5 seconds
- **THEN** the command SHALL return an error string

### Requirement: download_whisper_model command
The system SHALL provide a `download_whisper_model` command that sends `{ "command": "download_model" }` to the sidecar and returns immediately. Progress SHALL arrive via events.

#### Scenario: Model download initiated
- **WHEN** the frontend invokes `download_whisper_model`
- **THEN** the sidecar SHALL receive the download command and emit `model_progress` events

### Requirement: get_app_version command
The system SHALL provide a `get_app_version` synchronous command that returns `env!("CARGO_PKG_VERSION")`.

#### Scenario: Version query
- **WHEN** the frontend invokes `get_app_version`
- **THEN** it SHALL return the version string from Cargo.toml (e.g., `"1.0.0"`)
