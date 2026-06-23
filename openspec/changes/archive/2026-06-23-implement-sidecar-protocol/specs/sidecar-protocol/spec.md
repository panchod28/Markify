## ADDED Requirements

### Requirement: read_message from stdin
The system SHALL provide a `read_message()` function that reads one line from `sys.stdin`, strips whitespace, parses as JSON, and returns a dict. It SHALL raise `EOFError` if stdin is closed and `JSONDecodeError` if the JSON is invalid.

#### Scenario: Valid JSON received
- **WHEN** stdin contains `{"command":"convert"}\n`
- **THEN** `read_message()` SHALL return `{"command": "convert"}`

#### Scenario: stdin closed
- **WHEN** stdin reaches EOF
- **THEN** `read_message()` SHALL raise `EOFError`

### Requirement: write_message to stdout
The system SHALL provide a `write_message()` function that serializes a dict to JSON with `ensure_ascii=False`, appends `\n`, writes to `sys.stdout`, and calls `sys.stdout.flush()` immediately.

#### Scenario: Write a message
- **WHEN** `write_message({"type": "file_result", "payload": {...}})` is called
- **THEN** one line of JSON SHALL be written to stdout and the buffer SHALL be flushed

#### Scenario: Unicode content preserved
- **WHEN** the message contains Spanish characters (á, ñ, ü)
- **THEN** they SHALL be preserved as-is (not escaped) thanks to `ensure_ascii=False`

### Requirement: No print() to stdout
The system SHALL NEVER use `print()` for protocol messages. All protocol output SHALL go through `write_message()`. Debug messages SHALL use `print(..., file=sys.stderr)`.

#### Scenario: Debug logging
- **WHEN** a debug message needs to be logged
- **THEN** it SHALL be written to `sys.stderr`, NEVER to `sys.stdout`
