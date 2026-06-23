## ADDED Requirements

### Requirement: Stdin loop with command dispatch
The system SHALL provide a `main()` function that loops reading JSON messages from stdin and dispatches by `command` field: `convert`, `cancel`, `check_model`, `download_model`.

#### Scenario: Convert command received
- **WHEN** stdin receives `{"command": "convert", "payload": {"files": [...], "lang": "es"}}`
- **THEN** `handle_convert()` SHALL be called, cancel flag SHALL be cleared

#### Scenario: Cancel command received
- **WHEN** stdin receives `{"command": "cancel"}`
- **THEN** the cancel flag SHALL be set via `_cancel_flag.set()`

#### Scenario: Unknown command
- **WHEN** stdin receives a command with unknown type
- **THEN** a message SHALL be logged to stderr and the loop SHALL continue

### Requirement: Graceful shutdown on EOF
The system SHALL exit cleanly when stdin is closed (Tauri terminates the process).

#### Scenario: Tauri closes the pipe
- **WHEN** `read_message()` raises `EOFError`
- **THEN** the main loop SHALL break and the process SHALL exit with code 0

### Requirement: Global cancel flag
The system SHALL use a `threading.Event` as a global cancel flag that is checked before processing each file.

#### Scenario: Cancel during batch
- **WHEN** a `cancel` command arrives while processing a batch of 5 files
- **THEN** the current file SHALL finish, subsequent files SHALL be skipped, and `conversion_cancelled` SHALL be emitted

### Requirement: handle_convert processes files sequentially
The system SHALL process files one at a time, emitting `file_progress` at start, `file_result` on completion/error, and `conversion_complete` after all files.

#### Scenario: Three files processed
- **WHEN** a batch of 3 files is received
- **THEN** 3 `file_progress` messages (start), 3 `file_result` messages (results), and 1 `conversion_complete` SHALL be emitted

#### Scenario: Error in one file
- **WHEN** file 2 of 3 fails
- **THEN** file 3 SHALL still be processed and `conversion_complete` SHALL be emitted

### Requirement: handle_download_model with progress
The system SHALL download the Whisper model with a progress callback that emits `model_progress` messages.

#### Scenario: Model download succeeds
- **WHEN** the model downloads completely
- **THEN** `model_ready` SHALL be emitted

#### Scenario: Model download fails
- **WHEN** the download raises an exception
- **THEN** `model_error` SHALL be emitted with the error message
