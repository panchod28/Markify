## ADDED Requirements

### Requirement: save_markdown command
The system SHALL provide a `save_markdown` command that opens a native save dialog filtered for `.md` files, writes content to the chosen path, and returns the path or `null` if cancelled.

#### Scenario: User saves a markdown file
- **WHEN** `save_markdown` is invoked with content and suggested name `"mi_archivo.md"`
- **THEN** a save dialog SHALL appear with the suggested name and `.md` filter, and the content SHALL be written to the chosen path

#### Scenario: User cancels save dialog
- **WHEN** the user clicks Cancel in the save dialog
- **THEN** the command SHALL return `Ok(None)`

### Requirement: save_zip command
The system SHALL provide a `save_zip` command that creates a ZIP archive with all completed files using `Deflated` compression and saves via native dialog.

#### Scenario: Export multiple files as ZIP
- **WHEN** `save_zip` is invoked with 3 files and suggested name `"conversion_2026-06-22.zip"`
- **THEN** a ZIP archive SHALL be created containing 3 entries with their markdown content

#### Scenario: User cancels ZIP save
- **WHEN** the user clicks Cancel in the ZIP save dialog
- **THEN** the command SHALL return `Ok(None)` without creating any file

### Requirement: open_in_folder command
The system SHALL provide an `open_in_folder` command that opens the system file manager with the given file selected (macOS: `open -R`, Windows: `explorer /select`, Linux: `xdg-open`).

#### Scenario: Reveal file in Finder on macOS
- **WHEN** `open_in_folder("/Users/juan/output.md")` is called on macOS
- **THEN** Finder SHALL open with `output.md` selected

#### Scenario: Reveal file in Explorer on Windows
- **WHEN** `open_in_folder("C:\\output\\file.md")` is called on Windows
- **THEN** Explorer SHALL open with `file.md` selected

#### Scenario: Open folder on Linux
- **WHEN** `open_in_folder("/home/juan/output/file.md")` is called on Linux
- **THEN** `xdg-open` SHALL be called with the parent directory
