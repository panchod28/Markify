# Spec 06 — Component Catalog
> Markify — Especificación completa de cada componente React.
> Archivos destino: `src/components/`
> Dependencias: spec `01-types.md`, spec `02-design-system.md`, spec `03-stores.md`

---

## Reglas generales de componentes

1. **Todos los componentes son functional components con TypeScript.**
2. **Props siempre tipadas con `interface`, nunca con `type` para props.**
3. **Usar `cn()` de `src/lib/cn.ts` para combinar clases.**
4. **Nunca acceder al store directamente desde componentes presentacionales** — recibir datos por props. Solo los componentes contenedores/de-página acceden al store.
5. **Animaciones con Framer Motion** (`motion.div`, etc.). Las transiciones de entrada/salida usan `AnimatePresence`.
6. **Iconos solo de Lucide React** — `import { IconName } from 'lucide-react'`. Tamaño por defecto: 16px. Explícito cuando difiere.
7. **Todos los textos de usuario pasan por `useTranslation()`** — nunca strings hardcodeados en componentes.

---

## 1. Layout — `AppShell`

**Archivo:** `src/components/layout/AppShell.tsx`

**Responsabilidad:** Wrapper principal. Aplica el tema al DOM, monta los eventos Tauri, renderiza el Header y el contenido dinámico.

**Props:**
```typescript
interface AppShellProps {
  children: React.ReactNode;
}
```

**Comportamiento:**
- Al montar: llama `useAppStore.getState()._initialize()` para cargar preferencias guardadas.
- Al montar: invoca el hook `useTauriEvents()` para suscribirse a todos los eventos del sidecar.
- Al montar: invoca el hook `useSystemTheme()` para aplicar el tema al `<html>`.
- Al montar: llama `useConversionStore.getState().checkWhisperModel()`.
- Aplica `data-theme={resolvedTheme}` al `document.documentElement`.
- Renderiza: `<Header />` fijo arriba + `<main>` con el `children`.

**Estructura DOM:**
```
<div className="flex flex-col h-screen bg-bg overflow-hidden">
  <Header />
  <main className="flex-1 overflow-hidden">
    {children}
  </main>
</div>
```

---

## 2. Layout — `Header`

**Archivo:** `src/components/layout/Header.tsx`

**Responsabilidad:** Barra superior con logo, ThemeToggle y LanguageToggle.

**Props:** ninguna (lee del store).

**Altura:** exactamente 48px.

**Estructura DOM:**
```
<header className="
  h-12 flex items-center justify-between
  px-4 border-b border-border
  bg-surface
  // En macOS: padding-left: 76px para respetar el área del semáforo
">
  {/* Izquierda: logo */}
  <div className="flex items-center gap-2">
    <AppIcon size={20} />
    <span className="text-base font-semibold text-text-primary">Markify</span>
  </div>

  {/* Derecha: controles */}
  <div className="flex items-center gap-1">
    <ThemeToggle />
    <div className="w-px h-4 bg-border mx-1" /> {/* separador */}
    <LanguageToggle />
  </div>
</header>
```

**Nota macOS:** Detectar si es macOS con `navigator.platform.includes('Mac')` o mediante Tauri. Si es macOS, aplicar `pl-[76px]` para no solapar los botones del semáforo.

---

## 3. `ThemeToggle`

**Archivo:** `src/components/layout/ThemeToggle.tsx`

**Props:** ninguna.

**Estado leído del store:** `theme`, `resolvedTheme`.

**Comportamiento:**
- Muestra ícono `Sun` (20px) cuando `resolvedTheme === 'dark'` (para cambiar a light).
- Muestra ícono `Moon` (20px) cuando `resolvedTheme === 'light'` (para cambiar a dark).
- Ciclo de clicks: `light → dark → system → light → ...`
- Tooltip que muestra el modo actual: "Claro" / "Oscuro" / "Sistema".
- El cambio de ícono tiene transición de opacidad (150ms).

**Estilo:** botón ghost 32×32px, `border-radius: var(--radius-md)`.

---

## 4. `LanguageToggle`

**Archivo:** `src/components/layout/LanguageToggle.tsx`

**Props:** ninguna.

**Estado leído del store:** `language`, `resolvedLanguage`.

**Comportamiento:**
- Muestra `"ES"` cuando `resolvedLanguage === 'es'`, `"EN"` cuando `=== 'en'`.
- Click alterna entre `'es'` y `'en'` (nunca vuelve a `'system'` manualmente).
- Al cambiar, llama `i18n.changeLanguage(lang)` además de actualizar el store.

**Estilo:** botón ghost, texto `text-sm font-medium`, misma altura que ThemeToggle.

---

## 5. `DropZone` — Versión completa (estado empty)

**Archivo:** `src/components/dropzone/DropZone.tsx`

**Props:**
```typescript
interface DropZoneProps {
  onFilesAdded: (files: File[]) => void;
}
```

**Comportamiento:**
- Usa `react-dropzone` con configuración:
  ```typescript
  useDropzone({
    onDrop: (acceptedFiles) => onFilesAdded(acceptedFiles),
    noClick: true,   // El click lo maneja el botón "Seleccionar archivos"
    multiple: true,
    accept: {
      // Mapear las extensiones soportadas al formato react-dropzone
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      // ... etc para todas las extensiones de SUPPORTED_EXTENSIONS
      // Para audio usar 'audio/*': ['.mp3', '.wav', ...]
      // Para video usar 'video/*': ['.mp4', '.webm']
    },
  })
  ```
- **Estado normal:** borde dashed, fondo sutil, ícono + texto.
- **Estado drag-over (`isDragActive`):**
  - Borde: solid `var(--color-dropzone-border-active)`
  - Fondo: `var(--color-dropzone-bg-active)`
  - Ícono: scale 1.1 (Framer Motion spring)
  - Texto cambia a la clave i18n `dropzone.dragActive`
- El botón "Seleccionar archivos" dentro del dropzone abre el file picker:
  ```typescript
  // Crear input oculto con ref y hacer .click()
  const inputRef = useRef<HTMLInputElement>(null);
  const handleSelectClick = () => inputRef.current?.click();
  ```

**Estructura DOM:**
```
<div {...getRootProps()} className="
  flex flex-col items-center justify-center
  w-full max-w-[560px] mx-auto
  rounded-lg border-2 border-dashed
  border-[var(--color-dropzone-border)]
  bg-[var(--color-dropzone-bg)]
  px-8 py-12
  transition-all duration-[150ms]
  cursor-default
  select-none
  // cuando isDragActive:
  // border-solid border-[var(--color-dropzone-border-active)] bg-[var(--color-dropzone-bg-active)]
">
  <input {...getInputProps()} ref={inputRef} className="hidden" />

  {/* Ícono */}
  <motion.div animate={{ scale: isDragActive ? 1.1 : 1 }} transition={{ type: 'spring' }}>
    <FileUp size={64} className="text-accent opacity-60 mb-4" />
  </motion.div>

  {/* Textos */}
  <h2 className="text-2xl font-semibold text-text-primary mb-2">
    {isDragActive ? t('dropzone.dragActive') : t('dropzone.title')}
  </h2>
  <p className="text-sm text-text-secondary mb-6">{t('dropzone.subtitle')}</p>

  {/* Botón seleccionar */}
  {!isDragActive && (
    <button onClick={handleSelectClick} className="/* ghost button styles */">
      {t('fileList.selectFiles')}
    </button>
  )}

  {/* Formatos soportados */}
  <p className="text-xs text-text-tertiary mt-4">{t('dropzone.supported')}</p>
</div>
```

---

## 6. `DropZoneCompact` — Versión pequeña (estado files-ready)

**Archivo:** `src/components/dropzone/DropZoneCompact.tsx`

**Props:**
```typescript
interface DropZoneCompactProps {
  onFilesAdded: (files: File[]) => void;
}
```

**Comportamiento:** igual que `DropZone` pero:
- `noClick: false` — toda el área es clickeable.
- Diseño horizontal, compacto (40px alto).
- Solo muestra ícono `Plus` + texto "Añadir más archivos".
- Sin ícono grande ni subtexto de formatos.

---

## 7. `FileItem` — Ítem de archivo en lista pre-conversión

**Archivo:** `src/components/files/FileItem.tsx`

**Props:**
```typescript
interface FileItemProps {
  file: ConversionFile;
  onRemove: (id: string) => void;
}
```

**Alto:** 64px fijo.

**Animaciones:**
- Entrada: `slideInUp` (200ms, ease-out). Usar `motion.div` con `initial={{ opacity: 0, y: 8 }}` y `animate={{ opacity: 1, y: 0 }}`.
- Salida: `motion.div` con `exit={{ opacity: 0, x: -8, height: 0 }}` (200ms). Envolver en `AnimatePresence`.

**Estructura DOM:**
```
<motion.div className="
  flex items-center gap-3
  px-4 py-2 h-16
  rounded-md
  hover:bg-surface-secondary
  transition-colors duration-[100ms]
  group
">
  {/* Ícono de tipo de archivo */}
  <div className="flex-shrink-0">
    <FileIcon extension={file.extension} size={32} />
  </div>

  {/* Info del archivo */}
  <div className="flex-1 min-w-0">
    <p className="text-base font-medium text-text-primary truncate">
      {file.originalName}
    </p>
    <p className="text-xs text-text-secondary truncate">
      {t('fileList.sanitizedName')} {file.sanitizedName}
      <span className="mx-2">·</span>
      {file.formattedSize}
    </p>
  </div>

  {/* Botón eliminar — visible solo en hover */}
  <button
    onClick={() => onRemove(file.id)}
    className="
      opacity-0 group-hover:opacity-100
      flex-shrink-0 w-8 h-8
      flex items-center justify-center
      rounded-md text-text-tertiary
      hover:text-error hover:bg-error-subtle
      transition-all duration-[100ms]
    "
    aria-label={t('fileList.removeFile')}
  >
    <X size={16} />
  </button>
</motion.div>
```

---

## 8. `FileList` — Lista de archivos pre-conversión

**Archivo:** `src/components/files/FileList.tsx`

**Props:**
```typescript
interface FileListProps {
  files: ConversionFile[];
  onRemove: (id: string) => void;
  onClearAll: () => void;
  onAddMore: (files: File[]) => void;
  onConvert: () => void;
  isConvertDisabled: boolean;
}
```

**Estructura DOM:**
```
<div className="flex flex-col h-full">
  {/* Header de la lista */}
  <div className="flex items-center justify-between px-4 py-3 border-b border-border">
    <span className="text-sm font-semibold text-text-primary">
      {t('fileList.filesCount', { count: files.length })}
    </span>
    <button onClick={onClearAll} className="/* ghost destructive */">
      {t('fileList.clearAll')}
    </button>
  </div>

  {/* Lista con scroll */}
  <ScrollArea className="flex-1">
    <AnimatePresence initial={false}>
      {files.map(file => (
        <FileItem key={file.id} file={file} onRemove={onRemove} />
      ))}
    </AnimatePresence>
  </ScrollArea>

  {/* Footer con acciones */}
  <div className="flex items-center justify-between px-4 py-3 border-t border-border">
    <DropZoneCompact onFilesAdded={onAddMore} />
    <button
      onClick={onConvert}
      disabled={isConvertDisabled}
      className="/* primary button */"
    >
      {t('fileList.convert')}
      <ChevronRight size={16} className="ml-1" />
    </button>
  </div>
</div>
```

---

## 9. `ProcessingFileItem` — Ítem durante conversión

**Archivo:** `src/components/conversion/ProcessingFileItem.tsx`

**Props:**
```typescript
interface ProcessingFileItemProps {
  file: ConversionFile;
}
```

**Alto:** 72px.

**Comportamiento por status:**
- `pending`: barra gris sin animación, badge gris "En espera", opacidad normal.
- `processing`: barra con shimmer animado, badge azul "Procesando", opacidad 100%.
- `completed`: barra verde completa (100%), badge verde con check, opacidad 70% (para dar foco al actual).
- `error`: barra roja completa, badge rojo con X, mensaje de error visible debajo del nombre.

**Estructura DOM:**
```
<div className="flex flex-col gap-1.5 px-4 py-3">
  <div className="flex items-center gap-3">
    <FileIcon extension={file.extension} size={24} />

    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-text-primary truncate">
        {file.originalName}
      </p>
      {file.status === 'error' && file.errorMessage && (
        <p className="text-xs text-error mt-0.5">{file.errorMessage}</p>
      )}
    </div>

    <StatusBadge status={file.status} />
  </div>

  {/* Progress bar */}
  <ProgressBar
    progress={file.progress}
    status={file.status}
    className="mt-1"
  />
</div>
```

---

## 10. `ProgressBar`

**Archivo:** `src/components/conversion/ProgressBar.tsx`

**Props:**
```typescript
interface ProgressBarProps {
  progress: number;    // 0-100
  status: FileStatus;
  className?: string;
}
```

**Renderizado:**
```
<div className={cn("h-1 rounded-sm bg-border overflow-hidden", className)}>
  <div
    className={cn(
      "h-full rounded-sm transition-all",
      {
        // processing sin progress real → shimmer
        "progress-shimmer w-full": status === 'processing' && progress === 0,
        // processing con progress real → barra de acento
        "bg-accent": status === 'processing' && progress > 0,
        // completado → verde
        "bg-success w-full": status === 'completed',
        // error → rojo
        "bg-error w-full": status === 'error',
        // pending → invisible
        "w-0": status === 'pending',
      }
    )}
    style={
      status === 'processing' && progress > 0
        ? { width: `${progress}%`, transition: 'width 300ms ease-out' }
        : undefined
    }
  />
</div>
```

---

## 11. `StatusBadge`

**Archivo:** `src/components/conversion/StatusBadge.tsx`

**Props:**
```typescript
interface StatusBadgeProps {
  status: FileStatus;
}
```

Ver spec `02-design-system.md` § 8 para los colores exactos.

**Íconos por status:**
- `pending`: `Clock` (16px)
- `processing`: spinner SVG animado (16px) — NO usar un ícono de Lucide estático
- `completed`: `CheckCircle` (16px)
- `error`: `XCircle` (16px)

**Spinner SVG para processing:**
```tsx
<svg className="animate-spin" width="16" height="16" viewBox="0 0 16 16">
  <circle
    cx="8" cy="8" r="6"
    fill="none" stroke="currentColor" strokeWidth="2"
    strokeDasharray="25" strokeDashoffset="10"
  />
</svg>
```

---

## 12. `GlobalProgress`

**Archivo:** `src/components/conversion/GlobalProgress.tsx`

**Props:**
```typescript
interface GlobalProgressProps {
  summary: ConversionSummary;
}
```

**Renderizado:**
```
<div className="px-4 py-3 flex items-center gap-2">
  {/* Spinner pequeño */}
  <svg className="animate-spin" width="14" height="14" .../>

  <span className="text-sm text-text-secondary">
    {t('processing.progress', {
      completed: summary.completed,
      total: summary.total
    })}
  </span>
</div>
```

---

## 13. `ProcessingView` — Vista completa durante conversión

**Archivo:** `src/components/conversion/ProcessingView.tsx`

**Props:**
```typescript
interface ProcessingViewProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  isCancelling: boolean;
  onCancel: () => void;
}
```

**Estructura DOM:**
```
<div className="flex flex-col h-full">
  <GlobalProgress summary={summary} />

  <ScrollArea className="flex-1">
    {files.map(file => (
      <ProcessingFileItem key={file.id} file={file} />
    ))}
  </ScrollArea>

  <div className="flex justify-end px-4 py-3 border-t border-border">
    <button
      onClick={onCancel}
      disabled={isCancelling}
      className="/* destructive secondary button */"
    >
      {isCancelling
        ? t('processing.cancelling')
        : t('processing.cancel')}
    </button>
  </div>
</div>
```

---

## 14. `ResultsView` — Vista de resultados

**Archivo:** `src/components/results/ResultsView.tsx`

**Props:**
```typescript
interface ResultsViewProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  selectedFileId: string | null;
  onSelectFile: (id: string) => void;
  onSave: () => Promise<void>;
  onRetryFailed: () => void;
  onNewConversion: () => void;
  viewMode: PreviewViewMode;
  onToggleViewMode: () => void;
}
```

**Layout:**
```
<div className="flex h-full">
  {/* Sidebar */}
  <ResultsSidebar
    className="w-[280px] flex-shrink-0 border-r border-border"
    files={files}
    summary={summary}
    selectedFileId={selectedFileId}
    onSelectFile={onSelectFile}
  />

  {/* Preview */}
  <div className="flex-1 flex flex-col overflow-hidden">
    <PreviewPanel
      content={selectedFile?.markdownContent ?? null}
      viewMode={viewMode}
      onToggleViewMode={onToggleViewMode}
    />
  </div>

  {/* ActionBar en el pie */}
  // Ver ResultsActionBar
</div>
```

**Nota:** el ActionBar va en la parte inferior del wrapper, no dentro del split. Usar `flex-col` en el wrapper externo.

---

## 15. `ResultsSidebar`

**Archivo:** `src/components/results/ResultsSidebar.tsx`

**Props:**
```typescript
interface ResultsSidebarProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  selectedFileId: string | null;
  onSelectFile: (id: string) => void;
  className?: string;
}
```

**Estructura DOM:**
```
<div className={cn("flex flex-col", className)}>
  {/* Resumen */}
  <div className="px-4 py-4 border-b border-border">
    <div className="flex items-center gap-2 mb-1">
      <CheckCircle size={20} className="text-success" />
      <span className="text-base font-semibold text-text-primary">
        {t('results.successAll', { count: summary.completed })}
      </span>
    </div>
    {summary.failed > 0 && (
      <p className="text-sm text-error">
        {t('results.failedCount', { count: summary.failed })}
      </p>
    )}
  </div>

  {/* Lista de archivos resultado */}
  <ScrollArea className="flex-1">
    {files.map(file => (
      <ResultFileItem
        key={file.id}
        file={file}
        isSelected={file.id === selectedFileId}
        onClick={() => file.status === 'completed' && onSelectFile(file.id)}
      />
    ))}
  </ScrollArea>
</div>
```

---

## 16. `ResultFileItem`

**Archivo:** `src/components/results/ResultFileItem.tsx`

**Props:**
```typescript
interface ResultFileItemProps {
  file: ConversionFile;
  isSelected: boolean;
  onClick: () => void;
}
```

**Comportamiento:**
- Solo los archivos con `status === 'completed'` son clickeables y seleccionables.
- Los archivos con `status === 'error'` muestran el mensaje de error debajo del nombre. No son clickeables.
- El ítem seleccionado tiene fondo `var(--color-accent-subtle)`.

---

## 17. `PreviewPanel`

**Archivo:** `src/components/results/PreviewPanel.tsx`

**Props:**
```typescript
interface PreviewPanelProps {
  content: string | null;
  viewMode: PreviewViewMode;
  onToggleViewMode: () => void;
}
```

**Comportamiento:**
- Si `content === null`: muestra estado vacío: ícono `FileText` + texto `t('preview.selectFile')`.
- Si `viewMode === 'rendered'`: renderiza con `<ReactMarkdown remarkPlugins={[remarkGfm]}>`. Aplicar clase `markdown-preview` (ver spec `02-design-system.md` § 10).
- Si `viewMode === 'raw'`: renderiza `<pre><code>{content}</code></pre>` con fuente mono.

**Toolbar:**
```
<div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface">
  <span className="text-xs text-text-tertiary">{sanitizedName}</span>
  <div className="flex gap-1">
    <button
      onClick={onToggleViewMode}
      className={cn("/* ghost small */", viewMode === 'rendered' && "bg-accent-subtle text-accent")}
    >
      {t('preview.rendered')}
    </button>
    <button
      onClick={onToggleViewMode}
      className={cn("/* ghost small */", viewMode === 'raw' && "bg-accent-subtle text-accent")}
    >
      {t('preview.raw')}
    </button>
  </div>
</div>
```

---

## 18. `FileIcon`

**Archivo:** `src/components/ui/FileIcon.tsx`

**Props:**
```typescript
interface FileIconProps {
  extension: string;
  size?: number; // default: 24
  className?: string;
}
```

**Comportamiento:** Consulta `FILE_ICON_MAP` de `src/types/index.ts`. Si la extensión no está en el mapa, usa `FileText` con `text-gray-400`.

---

## 19. `WhisperModelModal`

**Archivo:** `src/components/modals/WhisperModelModal.tsx`

**Props:**
```typescript
interface WhisperModelModalProps {
  open: boolean;
  isDownloading: boolean;
  downloadProgress: number;     // 0-100
  downloadedMB: number;
  totalMB: number;
  downloadError: string | null;
  onConfirm: () => void;
  onDismiss: () => void;
}
```

**Fases del modal:**

1. **`!isDownloading && !downloadError`** → muestra descripción + botones "Cancelar" y "Descargar y continuar".
2. **`isDownloading`** → muestra barra de progreso y texto "Descargando...". Botones ocultos. **No se puede cerrar con click fuera ni Escape.**
3. **`downloadError`** → muestra mensaje de error + botones "Cancelar" y "Reintentar".

**Overlay:** `<dialog>` nativo o `shadcn/ui Dialog` con `onOpenChange` bloqueado durante descarga.

**Ancho:** 400px máximo. Centrado vertical y horizontal.

```
<Dialog open={open} onOpenChange={isDownloading ? undefined : onDismiss}>
  <DialogContent className="max-w-[400px]">
    <div className="flex flex-col items-center gap-4 py-4">
      <Brain size={48} className="text-accent" /> {/* ícono del modelo */}

      <div className="text-center">
        <h2 className="text-xl font-semibold mb-2">{t('whisperModal.title')}</h2>
        <p className="text-sm text-text-secondary">{t('whisperModal.description')}</p>
      </div>

      {isDownloading && (
        <div className="w-full">
          <ProgressBar progress={downloadProgress} status="processing" />
          <p className="text-xs text-text-secondary text-center mt-2">
            {t('whisperModal.progress', { percent: downloadProgress,
              downloaded: downloadedMB, total: totalMB })}
          </p>
        </div>
      )}

      {!isDownloading && (
        <div className="flex gap-2 w-full">
          <button onClick={onDismiss} className="flex-1 /* secondary */">
            {t('whisperModal.cancel')}
          </button>
          <button onClick={onConfirm} className="flex-1 /* primary */">
            {t('whisperModal.downloadAndContinue')}
          </button>
        </div>
      )}
    </div>
  </DialogContent>
</Dialog>
```

---

## 20. `ConfirmDialog`

**Archivo:** `src/components/modals/ConfirmDialog.tsx`

**Props:**
```typescript
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  dismissLabel: string;
  variant?: 'default' | 'destructive'; // default: 'default'
  onConfirm: () => void;
  onDismiss: () => void;
}
```

**Uso:** Confirmación de "¿Cancelar conversión?" y "¿Limpiar lista?".

---

## 21. `ValidationErrorToast`

**Archivo:** `src/components/ui/ValidationErrorToast.tsx`

**Props:**
```typescript
interface ValidationErrorToastProps {
  errors: FileValidationError[];
  onDismiss: () => void;
}
```

**Comportamiento:**
- Aparece en la esquina inferior derecha cuando `validationErrors.length > 0`.
- Auto-desaparece después de 5 segundos.
- Muestra hasta 3 errores; si hay más, muestra "y X más...".
- Usar `AnimatePresence` para entrada/salida.

**Mensajes por tipo de error:**
- `unsupported`: `t('errors.unsupportedFormat', { ext: error.ext })`
- `too_large`: `t('errors.fileTooBig')`
- `batch_too_large`: `t('errors.batchTooBig')`
- `too_many_files`: `t('errors.tooManyFiles')`
- `duplicate`: `t('errors.duplicate')`

---

## 22. `ResultsActionBar`

**Archivo:** `src/components/results/ResultsActionBar.tsx`

**Props:**
```typescript
interface ResultsActionBarProps {
  summary: ConversionSummary;
  savedPath: string | null;     // Path donde se guardó, o null
  onSave: () => Promise<void>;
  onRetryFailed: () => void;
  onNewConversion: () => void;
  onOpenInFolder: () => void;
}
```

**Comportamiento:**
- Si `summary.completed === 1`: botón "Guardar .md".
- Si `summary.completed > 1`: botón "Guardar ZIP".
- Si `summary.failed > 0`: botón "Reintentar fallidos".
- Si `savedPath !== null`: texto "Guardado en: [ruta]" + botón "Mostrar en carpeta".

---

## 23. `App.tsx` — Router de estados

```typescript
// src/App.tsx
// Conecta los stores con las vistas y gestiona las transiciones de estado.

import { AppShell } from '@/components/layout/AppShell';
import { DropZone } from '@/components/dropzone/DropZone';
import { FileList } from '@/components/files/FileList';
import { ProcessingView } from '@/components/conversion/ProcessingView';
import { ResultsView } from '@/components/results/ResultsView';
import { WhisperModelModal } from '@/components/modals/WhisperModelModal';
import { ConfirmDialog } from '@/components/modals/ConfirmDialog';
import { ValidationErrorToast } from '@/components/ui/ValidationErrorToast';
import { AnimatePresence, motion } from 'framer-motion';
import { useConversionStore } from '@/stores/useConversionStore';
import { usePreviewStore } from '@/stores/usePreviewStore';
import { useAppStore } from '@/stores/useAppStore';

export default function App() {
  const appState = useConversionStore(s => s.appState);
  // ... otros selectores del store

  return (
    <AppShell>
      <AnimatePresence mode="wait">
        {appState === 'empty' && (
          <motion.div key="empty" /* fade in/out */>
            <div className="flex items-center justify-center h-full p-8">
              <DropZone onFilesAdded={handleAddFiles} />
            </div>
          </motion.div>
        )}

        {appState === 'files-ready' && (
          <motion.div key="files-ready" /* fade in/out */>
            <FileList ... />
          </motion.div>
        )}

        {appState === 'processing' && (
          <motion.div key="processing" /* fade in/out */>
            <ProcessingView ... />
          </motion.div>
        )}

        {appState === 'results' && (
          <motion.div key="results" /* fade in/out */>
            <ResultsView ... />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modales — siempre montados, visibles según condición */}
      <WhisperModelModal ... />
      <ConfirmDialog ... />
      <ValidationErrorToast ... />
    </AppShell>
  );
}
```

**Transición entre estados:** `motion.div` con `initial={{ opacity: 0 }}` y `animate={{ opacity: 1 }}` (200ms). `AnimatePresence mode="wait"` espera que la vista saliente termine antes de mostrar la entrante.
