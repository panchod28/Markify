## ADDED Requirements

### Requirement: ProcessingFileItem with status-dependent rendering
The system SHALL render file items at 72px during conversion with icon, name, StatusBadge, and ProgressBar. Opacity SHALL be 100% for processing, 70% for completed, normal for others.

#### Scenario: Error state
- **WHEN** a file has `status === 'error'`
- **THEN** the error message SHALL be displayed below the file name in red

### Requirement: ProgressBar with 5 visual states
The system SHALL render a 4px bar that is invisible for pending, shimmer-animated for indeterminate processing, blue with width transition for known progress, green full for completed, red full for error.

#### Scenario: Indeterminate progress
- **WHEN** `status === 'processing'` and `progress === 0`
- **THEN** the bar SHALL use the `progress-shimmer` CSS class

### Requirement: StatusBadge with Lucide icons
The system SHALL show a 24px badge with: Clock (pending), animated SVG spinner (processing), CheckCircle green (completed), XCircle red (error).

#### Scenario: Processing badge
- **WHEN** `status === 'processing'`
- **THEN** an animated SVG spinner SHALL be displayed

### Requirement: GlobalProgress summary
The system SHALL show a small spinner with text "X of Y completed" during processing.

#### Scenario: 3 of 5 completed
- **WHEN** summary is `{ completed: 3, total: 5 }`
- **THEN** it SHALL display "3 de 5 completados"

### Requirement: ProcessingView with cancel
The system SHALL render GlobalProgress at top, a scrollable list of ProcessingFileItems, and a cancel button at bottom that shows "Cancelling..." while `isCancelling` is true.
