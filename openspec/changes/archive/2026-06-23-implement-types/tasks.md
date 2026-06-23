## 1. Core types and enums

- [x] 1.1 Create `src/types/index.ts` with union types (`FileCategory`, `FileStatus`, `AppState`, `Theme`, `ResolvedTheme`, `Language`, `ResolvedLanguage`, `PreviewViewMode`)
- [x] 1.2 Add `ConversionFile` interface with all fields (id, originalName, sanitizedName, path, sizeBytes, formattedSize, category, extension, status, progress, errorMessage?, markdownContent?)
- [x] 1.3 Add event payload interfaces (`ConversionProgressEvent`, `ModelDownloadProgressEvent`)
- [x] 1.4 Add `ConversionSummary` computed interface (total, completed, failed, pending)
- [x] 1.5 Add Tauri command payload interfaces (`StartConversionPayload`, `SaveZipPayload`)

## 2. Extension constants and icon map

- [x] 2.1 Add `DOCUMENT_EXTENSIONS` const array with `as const` and derive `DocumentExtension` type
- [x] 2.2 Add `AUDIO_EXTENSIONS` const array with `as const` and derive `AudioExtension` type
- [x] 2.3 Add `SUPPORTED_EXTENSIONS` const array (spread) and derive `SupportedExtension` type
- [x] 2.4 Add `FILE_ICON_MAP` record mapping each SupportedExtension to `{ icon, colorClass }`

## 3. Configuration constants

- [x] 3.1 Add file/batch limit constants (`MAX_FILE_SIZE_BYTES`, `MAX_TOTAL_BATCH_SIZE_BYTES`, `MAX_FILES_PER_BATCH`)
- [x] 3.2 Add Whisper model constants (`WHISPER_MODEL_NAME`, `WHISPER_MODEL_SIZE_MB`)
- [x] 3.3 Add window dimension constants (`WINDOW_DEFAULT_WIDTH`, `WINDOW_DEFAULT_HEIGHT`, `WINDOW_MIN_WIDTH`, `WINDOW_MIN_HEIGHT`)

## 4. File utility functions

- [x] 4.1 Create `src/lib/fileUtils.ts` with `getExtension()` function
- [x] 4.2 Add `isSupportedExtension()` type guard function
- [x] 4.3 Add `getFileCategory()` function returning `FileCategory | null`

## 5. Formatting utility functions

- [x] 5.1 Create `src/lib/formatters.ts` with `formatFileSize()` function
- [x] 5.2 Add `generateZipName()` function

## 6. Typed Tauri wrapper

- [x] 6.1 Create `src/lib/tauri.ts` with `tauriCommands` object (all 8 typed invoke wrappers)
- [x] 6.2 Add `tauriEvents` object (all 6 typed listen wrappers)
