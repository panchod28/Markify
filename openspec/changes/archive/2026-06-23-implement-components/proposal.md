## Why

Markify tiene types (01), design system (02) y stores (03). Ahora los componentes React son el paso 6 del orden de implementación. Son la capa visual completa: layout, dropzone, lista de archivos, vista de procesamiento, resultados con preview de markdown, modales y App.tsx como router de estados. Sin componentes, la app no tiene UI.

## What Changes

- Crear 22 componentes React + 1 App.tsx (23 total) en `src/components/`
- **Layout (4):** `AppShell`, `Header`, `ThemeToggle`, `LanguageToggle`
- **Dropzone (2):** `DropZone` (estado empty), `DropZoneCompact` (add more)
- **Archivos (2):** `FileItem`, `FileList`
- **Conversión (5):** `ProcessingFileItem`, `ProgressBar`, `StatusBadge`, `GlobalProgress`, `ProcessingView`
- **Resultados (4):** `ResultsView`, `ResultsSidebar`, `ResultFileItem`, `PreviewPanel`
- **UI/Modales (4):** `FileIcon`, `WhisperModelModal`, `ConfirmDialog`, `ValidationErrorToast`
- **Acciones (1):** `ResultsActionBar`
- **App.tsx:** Router de estados con AnimatePresence + conexión stores-vistas

## Capabilities

### New Capabilities

- `layout-components`: AppShell, Header, ThemeToggle, LanguageToggle
- `dropzone-components`: DropZone (react-dropzone) y DropZoneCompact
- `file-components`: FileItem con animaciones Framer Motion y FileList con ScrollArea
- `conversion-components`: ProcessingView, ProcessingFileItem, ProgressBar, StatusBadge, GlobalProgress
- `results-components`: ResultsView (split), ResultsSidebar, ResultFileItem, PreviewPanel (ReactMarkdown)
- `shared-ui`: FileIcon, WhisperModelModal, ConfirmDialog, ValidationErrorToast, ResultsActionBar, App.tsx router

### Modified Capabilities

N/A.

## Impact

- **Crea 23 archivos** en `src/components/` y `src/App.tsx`
- **Dependencias:** `react-dropzone`, `react-markdown`, `remark-gfm`, `framer-motion`, `lucide-react` (ya instaladas)
- **Tipos usados:** todos los de `src/types/index.ts`
- **Stores usados:** `useAppStore`, `useConversionStore`, `usePreviewStore`
- **i18n:** `useTranslation()` en todos los textos visibles
