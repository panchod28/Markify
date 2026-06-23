## Context

Los 23 componentes están implementados (spec 06). El spec 07 define refinamientos visuales exactos para cada estado de pantalla. Son ajustes puntuales de comportamiento y estilos.

## Goals / Non-Goals

**Goals:**
- Ajustar transiciones de App.tsx a las del spec (y: 6 enter, y: -4 exit)
- Añadir lógica de confirmación en FileList para 3+ archivos
- Añadir borde izquierdo accent en ítem seleccionado del sidebar
- Mejorar toast con borde izquierdo error y fondo elevated
- Vista "todos fallaron" en preview panel
- Accesibilidad: aria-live, aria-labels

**Non-Goals:**
- Crear nuevos componentes
- Persistencia de posición de ventana (requiere Rust)

## Decisions

1. **Transición unificada en App.tsx**: Un solo `motion.div` con variantes genéricas en lugar de transiciones diferentes por estado. El spec define una fórmula común: `initial={{ opacity: 0, y: 6 }}`, `exit={{ opacity: 0, y: -4 }}`.

2. **FileList clear usa `useState` local para el ConfirmDialog**: La lógica de "confirmar solo 3+" se maneja en FileList con un estado local de confirmación.

3. **ResultsSidebar borde izquierdo en seleccionado**: Añadir `border-l-[3px] border-l-accent` condicional al ResultFileItem cuando `isSelected`.

4. **PreviewPanel vista fallida**: Si todos los archivos son error (no hay completed), mostrar estado "todos fallaron" con FileX.
