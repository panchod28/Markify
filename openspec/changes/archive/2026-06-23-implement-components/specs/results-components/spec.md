## ADDED Requirements

### Requirement: ResultsView split layout
The system SHALL render a sidebar (280px) with ResultsSidebar and a preview area with PreviewPanel, plus ResultsActionBar at the bottom.

#### Scenario: File selected in sidebar
- **WHEN** a completed file is clicked in ResultsSidebar
- **THEN** its markdown SHALL appear in PreviewPanel

### Requirement: ResultsSidebar with summary
The system SHALL show a header with completed count + failed count, and a scrollable list of ResultFileItems. Only completed files are clickable.

#### Scenario: Mixed results
- **WHEN** 3 completed and 1 failed
- **THEN** the header SHALL show "3 archivos convertidos" and "1 error"

### Requirement: ResultFileItem selection
The system SHALL highlight the selected file with `accent-subtle` background. Failed files SHALL show error message and SHALL NOT be clickable.

#### Scenario: Select a completed file
- **WHEN** user clicks a completed ResultFileItem
- **THEN** `onSelectFile(file.id)` SHALL be called and the item SHALL highlight

### Requirement: PreviewPanel with ReactMarkdown
The system SHALL render markdown using `ReactMarkdown` with `remarkGfm` when `viewMode === 'rendered'`, and raw `<pre><code>` when `viewMode === 'raw'`. Empty state SHALL show a prompt to select a file.

#### Scenario: Rendered preview
- **WHEN** a file is selected and `viewMode === 'rendered'`
- **THEN** markdown SHALL be rendered with headings, code blocks, tables, etc.

#### Scenario: No file selected
- **WHEN** `content === null`
- **THEN** a FileText icon with "Select a file to preview" text SHALL be displayed

### Requirement: ResultsActionBar context-dependent buttons
The system SHALL show "Save .md" for single file, "Save ZIP" for multiple, "Retry failed" if errors exist, and "Show in folder" after save.

#### Scenario: Single completed file
- **WHEN** 1 file is completed and 0 failed
- **THEN** the action bar SHALL show "Save .md" button
