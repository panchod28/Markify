## 1. Layout Components

- [x] 1.1 Create `src/components/layout/AppShell.tsx` — wrapper with store init, Tauri events, theme hook, Whisper model check
- [x] 1.2 Create `src/components/layout/Header.tsx` — 48px bar with logo, macOS padding, theme/language toggles
- [x] 1.3 Create `src/components/layout/ThemeToggle.tsx` — Sun/Moon icon cycle, tooltip, opacity transition
- [x] 1.4 Create `src/components/layout/LanguageToggle.tsx` — ES/EN toggle with i18n sync

## 2. Dropzone Components

- [x] 2.1 Create `src/components/dropzone/DropZone.tsx` — full dropzone with react-dropzone, drag-active state, hidden file input
- [x] 2.2 Create `src/components/dropzone/DropZoneCompact.tsx` — compact horizontal variant for adding more files

## 3. File Components

- [x] 3.1 Create `src/components/files/FileIcon.tsx` — render Lucide icon from FILE_ICON_MAP by extension
- [x] 3.2 Create `src/components/files/FileItem.tsx` — 64px row with slideInUp animation, hover delete button
- [x] 3.3 Create `src/components/files/FileList.tsx` — header + scroll list + footer with DropZoneCompact and Convert button

## 4. Conversion Components

- [x] 4.1 Create `src/components/conversion/ProgressBar.tsx` — 5-state progress bar (pending/processing/completed/error + shimmer)
- [x] 4.2 Create `src/components/conversion/StatusBadge.tsx` — Clock/spinner/CheckCircle/XCircle badges
- [x] 4.3 Create `src/components/conversion/ProcessingFileItem.tsx` — 72px item with status badge + progress bar + error message
- [x] 4.4 Create `src/components/conversion/GlobalProgress.tsx` — spinner + "X of Y" summary text
- [x] 4.5 Create `src/components/conversion/ProcessingView.tsx` — GlobalProgress + scroll list + cancel button

## 5. Results Components

- [x] 5.1 Create `src/components/results/ResultFileItem.tsx` — selectable result item with completed/error states
- [x] 5.2 Create `src/components/results/ResultsSidebar.tsx` — 280px sidebar with summary header + result file list
- [x] 5.3 Create `src/components/results/PreviewPanel.tsx` — ReactMarkdown rendered / raw code view with toolbar
- [x] 5.4 Create `src/components/results/ResultsActionBar.tsx` — context-dependent save/retry/open buttons
- [x] 5.5 Create `src/components/results/ResultsView.tsx` — split layout combining sidebar + preview + action bar

## 6. Modals and App Router

- [x] 6.1 Create `src/components/modals/WhisperModelModal.tsx` — 3-phase model download dialog
- [x] 6.2 Create `src/components/modals/ConfirmDialog.tsx` — reusable confirmation dialog
- [x] 6.3 Create `src/components/ui/ValidationErrorToast.tsx` — auto-dismiss error toast
- [x] 6.4 Create `src/App.tsx` — state router with AnimatePresence connecting stores to views + modals
