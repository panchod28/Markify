## ADDED Requirements

### Requirement: start_conversion command
The system SHALL provide a `start_conversion` command that accepts `files: Vec<FilePayload>` and `lang: String`, constructs a JSON message with `command: "convert"`, writes it to the sidecar stdin, and returns immediately.

#### Scenario: Frontend starts conversion
- **WHEN** the frontend invokes `start_conversion` with 5 PDFs and `lang: "es"`
- **THEN** a JSON message SHALL be written to sidecar stdin and the command SHALL return `Ok(())`

#### Scenario: Sidecar not available
- **WHEN** the sidecar process is not running
- **THEN** `write_to_sidecar` SHALL fail and the command SHALL return an error string

### Requirement: cancel_conversion command
The system SHALL provide a `cancel_conversion` command that sends a `{ "command": "cancel" }` message to the sidecar stdin.

#### Scenario: User cancels during processing
- **WHEN** the frontend invokes `cancel_conversion`
- **THEN** a cancel message SHALL be written to sidecar stdin and the command SHALL return `Ok(())`

### Requirement: JSON message format for sidecar
The system SHALL format all sidecar messages as `{ "id": "<uuid>", "command": "<name>", "payload": { ... } }` with `\n` appended at the end.

#### Scenario: Conversion message
- **WHEN** sending a convert command
- **THEN** the JSON SHALL contain `"command": "convert"`, a UUID `"id"`, and the `"payload"` object

### Requirement: write_to_sidecar helper
The system SHALL provide a `write_to_sidecar` async function that appends `\n` to the message, locks the sidecar Mutex, writes to stdin, and returns `Result`.

#### Scenario: Writing a message
- **WHEN** `write_to_sidecar(&app, message)` is called
- **THEN** the message with trailing newline SHALL be written to the child process stdin
