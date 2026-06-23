## ADDED Requirements

### Requirement: Model path resolution
The system SHALL resolve the model path to `~/.markify/models/whisper/` in development mode and to the binary's parent directory when running as PyInstaller bundle (`sys.frozen`).

#### Scenario: Development mode
- **WHEN** `get_model_path()` is called and `sys.frozen` is `False`
- **THEN** it SHALL return `~/.markify/models/whisper/`

#### Scenario: PyInstaller bundle
- **WHEN** `get_model_path()` is called and `sys.frozen` is `True`
- **THEN** it SHALL return the directory containing `sys.executable`

### Requirement: Directory auto-creation
The system SHALL create the model directory if it does not exist.

#### Scenario: First run
- **WHEN** the model directory does not exist
- **THEN** it SHALL be created with `parents=True, exist_ok=True`

### Requirement: Model existence check
The system SHALL verify model existence by checking if the file `base.pt` exists at the model path and is larger than 100 MB.

#### Scenario: Model present
- **WHEN** `base.pt` exists and is >100 MB
- **THEN** `model_exists()` SHALL return `True`

#### Scenario: Partial download
- **WHEN** `base.pt` exists but is <100 MB
- **THEN** `model_exists()` SHALL return `False`

### Requirement: Model download with progress
The system SHALL download `base.pt` from the official Whisper repository using `urllib.request.urlretrieve` with a `reporthook` that calls the progress callback.

#### Scenario: Download progress
- **WHEN** the model is being downloaded
- **THEN** `progress_callback(percent, downloaded_mb, total_mb)` SHALL be called at regular intervals

#### Scenario: Download completes
- **WHEN** the download finishes successfully
- **THEN** the model file SHALL be at the model path

### Requirement: Download error cleanup
The system SHALL delete partial downloads on error.

#### Scenario: Network error during download
- **WHEN** `urlretrieve` raises `URLError`
- **THEN** any partial file SHALL be deleted and `ConnectionError` SHALL be raised with a Spanish message
