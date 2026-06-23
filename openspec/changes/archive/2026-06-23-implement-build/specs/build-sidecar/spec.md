## ADDED Requirements

### Requirement: PyInstaller build script with platform detection
The system SHALL provide `sidecar/build.py` that detects the current platform, generates the correct target triple, runs PyInstaller with `--onefile --console`, and outputs to `src-tauri/binaries/`.

#### Scenario: Build on Apple Silicon Mac
- **WHEN** `build.py` runs on `arm64` macOS
- **THEN** it SHALL output `markify-sidecar-aarch64-apple-darwin`

#### Scenario: Exclude heavy modules
- **WHEN** PyInstaller runs
- **THEN** matplotlib, PIL, tkinter, PyQt5, wx, notebook, IPython SHALL be excluded

### Requirement: Failed build exits with code 1
The system SHALL exit with code 1 if PyInstaller returns non-zero status.

#### Scenario: Build fails
- **WHEN** PyInstaller returns non-zero
- **THEN** `build.py` SHALL print error message and `sys.exit(1)`
