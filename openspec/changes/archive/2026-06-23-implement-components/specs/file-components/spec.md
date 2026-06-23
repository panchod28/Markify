## ADDED Requirements

### Requirement: FileItem with Framer Motion
The system SHALL render each file as a 64px row with extension icon, file name, sanitized name + size, and a hover-visible delete button. Entry animation SHALL be slideInUp, exit SHALL fade+shrink.

#### Scenario: File appears in list
- **WHEN** a file is added
- **THEN** it SHALL animate in with opacity 0→1 and translateY 8→0 over 200ms

#### Scenario: Remove button hover
- **WHEN** user hovers over a FileItem
- **THEN** the X button SHALL fade in with `group-hover:opacity-100`

### Requirement: FileList with scroll and actions
The system SHALL render a header with file count + clear button, a scrollable area with `AnimatePresence` wrapping FileItems, and a footer with DropZoneCompact + Convert button.

#### Scenario: Convert button disabled
- **WHEN** `isConvertDisabled` is true
- **THEN** the Convert button SHALL be disabled with reduced opacity
