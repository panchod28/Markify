## Why

Los componentes del spec 06 están implementados pero necesitan refinamiento visual y de comportamiento según las especificaciones de pantalla del spec 07. Esto incluye animaciones de transición correctas, confirmación de limpiar lista, estilos del sidebar de resultados, toast de errores con borde izquierdo, y comportamiento responsive. Son ajustes de polish que completan la experiencia visual Apple-quality.

## What Changes

- Ajustar animaciones de transición entre estados en App.tsx con valores exactos del spec (y: 6 → 0, exit: y: -4)
- Añadir lógica de confirmación en FileList: solo mostrar ConfirmDialog para 3+ archivos al limpiar
- Refinar ResultsSidebar: borde izquierdo 3px accent en ítem seleccionado
- Refinar ValidationErrorToast: borde izquierdo 3px error, fondo elevated surface
- Añadir vista "todos fallaron" en preview panel (estado vacío con ícono FileX)
- Añadir aria-live="polite" en GlobalProgress
- Añadir aria-labels en botones sin texto

## Capabilities

### New Capabilities

- `screen-polish`: Refinamientos visuales a componentes existentes: transiciones App.tsx, confirmación limpiar, sidebar selected border, toast borde, preview empty state, accesibilidad

### Modified Capabilities

N/A — son refinamientos de implementación, no cambios de requirements.

## Impact

- **Modifica:** `src/App.tsx`, `src/components/files/FileList.tsx`, `src/components/results/ResultsSidebar.tsx`, `src/components/results/PreviewPanel.tsx`, `src/components/ui/ValidationErrorToast.tsx`, `src/components/conversion/GlobalProgress.tsx`
