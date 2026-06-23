## Context

El spec `06-components.md` define 22 componentes + App.tsx con props exactas, estructura DOM, animaciones y comportamiento. Todos los tipos, stores y el design system ya están implementados. Este cambio es la capa visual completa.

## Goals / Non-Goals

**Goals:**
- Implementar los 23 componentes con sus props tipadas vía `interface`
- Usar Framer Motion para animaciones de entrada/salida con `AnimatePresence`
- Componentes presentacionales reciben datos por props; contenedores acceden al store
- Todos los textos via `useTranslation()`
- Iconos de `lucide-react`

**Non-Goals:**
- Modificar stores o tipos existentes
- Implementar i18n translation keys (spec 08)
- Crear la pantalla de configuración (no existe en spec)

## Decisions

1. **`AnimatePresence mode="wait"` en App.tsx**: Espera que la vista saliente termine su animación de salida antes de montar la entrante. Evita parpadeos.

2. **`useDropzone` configurado con los MIME types de `SUPPORTED_EXTENSIONS`**: El array `accept` se genera dinámicamente desde las constantes de tipos.

3. **ProgressBar con 5 estados visuales**: pending (invisible), processing sin progreso (shimmer), processing con progreso (barra azul), completed (verde), error (rojo).

4. **PreviewPanel con `ReactMarkdown` + `remarkGfm`**: Renderiza markdown con soporte GFM (tablas, strikethrough, etc.). La clase CSS `markdown-preview` ya está en `index.css`.

5. **WhisperModelModal no se puede cerrar durante descarga**: `onOpenChange` es `undefined` mientras `isDownloading`, bloqueando Escape y click fuera.

6. **macOS detection para Header padding**: `navigator.platform.includes('Mac')` para aplicar `pl-[76px]`.

## Risks / Trade-offs

- **[Bajo] i18n keys no existen aún**: Los componentes usan `t('key')` pero los JSON de traducción no se han creado (spec 08). Mitigación: react-i18next muestra la key como fallback.
- **[Medio] 23 archivos es mucho para una sesión**: Priorizar orden de implementación según dependencias (layout → dropzone → files → conversion → results → modals → App).
