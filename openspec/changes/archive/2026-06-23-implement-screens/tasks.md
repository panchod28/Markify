## 1. App Transitions

- [x] 1.1 Update `src/App.tsx` — unified motion.div with initial={{ y: 6 }}, exit={{ y: -4 }}, ease cubic-bezier

## 2. FileList Clear Confirmation

- [x] 2.1 Update `src/components/files/FileList.tsx` — add ConfirmDialog for clear when files.length >= 3

## 3. Results Sidebar Polish

- [x] 3.1 Update `src/components/results/ResultFileItem.tsx` — add left accent border on selected file
- [x] 3.2 Update `src/components/results/PreviewPanel.tsx` — add all-failed empty state view

## 4. Toast Polish

- [x] 4.1 Update `src/components/ui/ValidationErrorToast.tsx` — left error border, elevated surface bg

## 5. Accessibility

- [x] 5.1 Update `src/components/conversion/GlobalProgress.tsx` — add aria-live="polite"
- [x] 5.2 Update `src/components/layout/ThemeToggle.tsx` — add aria-label
