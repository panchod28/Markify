## ADDED Requirements

### Requirement: App.tsx unified transitions
The system SHALL use `initial={{ opacity: 0, y: 6 }}`, `animate={{ opacity: 1, y: 0 }}`, `exit={{ opacity: 0, y: -4 }}` with `duration: 0.2, ease: [0.4, 0, 0.2, 1]` for all state transitions.

#### Scenario: State changes from empty to files-ready
- **WHEN** `appState` transitions
- **THEN** the outgoing view SHALL fade up and the incoming view SHALL slide up 6px while fading in

### Requirement: FileList clear confirmation for 3+
The system SHALL clear files directly when count < 3. For 3 or more files, it SHALL show a ConfirmDialog before clearing.

#### Scenario: Clear 2 files
- **WHEN** user clicks "Limpiar todo" with 2 files
- **THEN** files SHALL be cleared immediately without confirmation

#### Scenario: Clear 5 files
- **WHEN** user clicks "Limpiar todo" with 5 files
- **THEN** a ConfirmDialog SHALL appear with "¿Limpiar la lista?" and file count

### Requirement: Selected item left border in sidebar
The system SHALL render a 3px left accent border on the selected ResultFileItem.

#### Scenario: File selected in sidebar
- **WHEN** `isSelected` is true
- **THEN** the item SHALL have `border-l-[3px] border-l-accent`

### Requirement: Toast left error border
The system SHALL render the ValidationErrorToast with a 3px left border in error color and elevated surface background.

#### Scenario: Validation error toast
- **WHEN** errors exist
- **THEN** the toast SHALL have `border-l-[3px] border-l-error bg-surface-elevated`

### Requirement: Preview all-failed state
The system SHALL show a FileX icon with "No se pudo convertir ningún archivo" text when all files are errors and none completed.

#### Scenario: All files failed
- **WHEN** summary.completed === 0 AND summary.failed > 0
- **THEN** the preview SHALL show an empty state with error messaging

### Requirement: Accessibility improvements
The system SHALL add `aria-live="polite"` to GlobalProgress and `aria-label` to all icon-only buttons (ThemeToggle, FileItem X).

#### Scenario: Screen reader announces progress
- **WHEN** GlobalProgress updates
- **THEN** a screen reader SHALL announce the updated completion count
