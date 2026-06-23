## 1. Dependencies

- [x] 1.1 Install `@tauri-apps/plugin-store` npm package

## 2. App Store

- [x] 2.1 Create `src/stores/useAppStore.ts` with `AppStore` interface, `INITIAL_STATE`, and `useAppStore` hook using `zustand` and `@tauri-apps/plugin-store`
- [x] 2.2 Implement `setTheme()` — updates state and persists to `markify-prefs.json`
- [x] 2.3 Implement `setLanguage()` — updates state and persists to `markify-prefs.json`
- [x] 2.4 Implement `_setResolvedTheme()` and `_setResolvedLanguage()` — simple setters
- [x] 2.5 Implement `_initialize()` — loads persisted preferences from store, falls back to initial values on error

## 3. Sanitizer Utility

- [x] 3.1 Create `src/lib/sanitizer.ts` with `sanitizeFilename()` function that lowercases, removes accents, replaces special chars with underscores, and changes extension to `.md`

## 4. Conversion Store

- [x] 4.1 Create `src/stores/useConversionStore.ts` with `FileValidationError` type, `ConversionStore` interface, `INITIAL_CONVERSION_STATE`, and `useConversionStore` hook
- [x] 4.2 Implement computed getters: `summary`, `hasAudioFiles`, `completedFiles`, `failedFiles`, `pendingFiles`, `allCompleted`, `totalBatchSizeBytes`
- [x] 4.3 Implement `addFiles()` — validates files against limits, creates `ConversionFile` objects, collects `FileValidationError` in array, updates `appState`
- [x] 4.4 Implement `removeFile()` — removes file by id, transitions to `empty` if list becomes empty
- [x] 4.5 Implement `clearAllFiles()` and `clearValidationErrors()`
- [x] 4.6 Implement `startConversion()` — resets all files to `pending`, transitions to `processing`, invokes Tauri command
- [x] 4.7 Implement `cancelConversion()` — sets `isCancelling`, invokes cancel command
- [x] 4.8 Implement `retryFailed()` — resets only error files to `pending`, transitions to `processing`, invokes conversion for failed subset
- [x] 4.9 Implement `checkWhisperModel()` and `startModelDownload()`
- [x] 4.10 Implement internal handlers: `_handleFileUpdate`, `_handleModelDownloadProgress`, `_handleModelDownloadComplete`, `_handleConversionComplete`, `_handleConversionCancelled`
- [x] 4.11 Implement `resetToEmpty()` — resets to initial state

## 5. Preview Store

- [x] 5.1 Create `src/stores/usePreviewStore.ts` with `PreviewStore` interface, initial state, and actions `selectFile`, `toggleViewMode`, `reset`

## 6. Tauri Events Hook

- [x] 6.1 Create `src/hooks/useTauriEvents.ts` — registers all 6 event listeners on mount, dispatches to `useConversionStore.getState()`, cleans up on unmount

## 7. Update Theme Hook

- [x] 7.1 Update `src/hooks/useSystemTheme.ts` — verify imports from `useAppStore` work correctly now that the store exists
