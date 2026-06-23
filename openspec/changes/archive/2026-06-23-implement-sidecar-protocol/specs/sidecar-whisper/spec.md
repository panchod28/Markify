## ADDED Requirements

### Requirement: Whisper transcription with cancel support
The system SHALL provide a `transcribe_audio()` function that loads the Whisper base model, transcribes the audio file, and respects a `cancel_flag` threading.Event.

#### Scenario: Successful transcription
- **WHEN** a valid audio file is transcribed
- **THEN** Markdown content with heading, metadata quote, and transcribed text SHALL be returned

#### Scenario: Cancel before transcription
- **WHEN** `cancel_flag.is_set()` before loading Whisper
- **THEN** an empty string SHALL be returned

#### Scenario: Cancel after transcription
- **WHEN** `cancel_flag.is_set()` after transcription completes
- **THEN** an empty string SHALL be returned

### Requirement: Progress emission at 50%
The system SHALL emit a progress update at 50% after transcription completes to indicate the formatting phase.

#### Scenario: Progress during transcription
- **WHEN** `transcribe_audio()` finishes Whisper execution
- **THEN** a `file_progress` message with `progress: 50` SHALL be written

### Requirement: Whisper configuration
The system SHALL use `verbose=False` (no stdout output), `language=None` (auto-detect), and `fp16=False` (CPU compatibility).

#### Scenario: Transcription parameters
- **WHEN** `model.transcribe()` is called
- **THEN** it SHALL use `verbose=False`, `language=None`, `fp16=False`

### Requirement: Error detection for no speech
The system SHALL detect audio files with no detectable speech and raise `ValueError("audio_too_short")`.

#### Scenario: Instrumental music file
- **WHEN** an audio file with no speech is transcribed
- **THEN** `ValueError("audio_too_short")` SHALL be raised

### Requirement: Markdown formatting for transcription output
The system SHALL format transcription output as Markdown with the filename as heading, a metadata blockquote with source info, and the text body.

#### Scenario: Transcription output format
- **WHEN** transcription completes
- **THEN** the output SHALL start with `# Transcripción: <stem>`, include a `> Transcripción generada...` blockquote, and contain the raw text
