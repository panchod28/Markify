# Spec 07 — Screen States & Visual Specifications
> Markify — Especificación visual exacta de cada estado de pantalla.
> Este spec es la referencia para implementar el layout y las interacciones visuales.
> Dependencias: spec `02-design-system.md`, spec `06-components.md`

---

## 1. Ventana principal

| Propiedad | Valor |
|-----------|-------|
| Ancho por defecto | 960px |
| Alto por defecto | 680px |
| Ancho mínimo | 800px |
| Alto mínimo | 600px |
| Posición inicial | Centrada en pantalla |
| Redimensionable | Sí — la UI es responsive dentro de los mínimos |
| Persistencia de posición | Sí — guardar en Tauri Store al mover/redimensionar |

**Estructura global de la ventana:**
```
┌──────────────────────────────────────────────────────┐  960px
│  HEADER (48px fijo)                                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  MAIN CONTENT (altura variable = ventana - 48px)     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 2. Header (presente en todos los estados)

```
┌──────────────────────────────────────────────────────┐ h=48px
│  [icon 20px] Markify          [🌙 32px] │ [ES 32px] │
│  ← 16px                         16px → 8px 4px 16px │
└──────────────────────────────────────────────────────┘
```

- Fondo: `var(--color-surface)`
- Borde inferior: `1px solid var(--color-border)`
- Padding horizontal: 16px (izquierda y derecha)
- **En macOS:** padding-left = 76px para el área del semáforo (botones de ventana)
- Logo: ícono SVG de la app (20×20px) + texto "Markify" en `font-semibold`
- Separador entre ThemeToggle y LanguageToggle: `1px` alto 16px, color `var(--color-border)`

---

## 3. Estado `empty` — Pantalla inicial

**Descripción:** Sin archivos seleccionados. Único elemento visible: la DropZone grande centrada.

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │ ← Header 48px
├──────────────────────────────────────────────────────┤
│                                                      │
│                                                      │
│         ┌────────────────────────────────┐           │
│         │                               │           │
│         │          [FileUp 64px]         │           │
│         │                               │           │
│         │   Arrastra tus archivos aquí  │           │ ← h2: text-2xl semibold
│         │                               │           │
│         │   o [Seleccionar archivos]    │           │ ← ghost button
│         │                               │           │
│         │   PDF, Word, Excel, PPT,      │           │ ← text-xs tertiary
│         │   audio y video               │           │
│         │                               │           │
│         └────────────────────────────────┘           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**DropZone specs:**
- Ancho máximo: 560px, centrada horizontalmente
- Padding: 48px vertical, 32px horizontal
- Borde: 2px dashed `var(--color-dropzone-border)`
- Fondo: `var(--color-dropzone-bg)`
- Border radius: `var(--radius-lg)` = 14px
- Centrada vertical y horizontalmente en el área disponible usando `flex items-center justify-center h-full`

**Estado drag-over:**
```
│         ┌────────────────────────────────┐           │
│         │ ← borde solid acento →        │           │
│         │   ← fondo más intenso →       │           │
│         │          [FileUp 64px]         │           │ ← scale: 1.1
│         │                               │           │
│         │      Suelta los archivos       │           │ ← texto cambia
│         │           aquí               │           │
│         │                               │           │
│         │   (botón "Seleccionar" oculto) │           │
│         └────────────────────────────────┘           │
```

**Transición drag-over:** 150ms ease-default. Todos los cambios (borde, fondo, escala) simultáneos.

---

## 4. Estado `files-ready` — Archivos listos para convertir

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Archivos (3)                     [Limpiar todo]    │ ← 16px padding, h=48px
│  ───────────────────────────────────────────────────│ ← border-b
│                                                      │
│  [📄 32px] Mi Presentación 2024.pptx     3.2 MB [✕] │ ← FileItem h=64px
│            Se guardará como: mi_presentacion_2024.md │
│  ───────────────────────────────────────────────────│
│  [🎵 32px] grabacion_reunion.mp3         45.1 MB [✕]│
│            Se guardará como: grabacion_reunion.md    │
│  ───────────────────────────────────────────────────│
│  [📊 32px] presupuesto_q1.xlsx           1.1 MB  [✕]│
│            Se guardará como: presupuesto_q1.md       │
│                                                      │
│  (scroll si hay más archivos)                        │
│                                                      │
│  ───────────────────────────────────────────────────│ ← border-t
│  [+ Añadir más archivos]          [  Convertir →  ] │ ← footer h=56px
└──────────────────────────────────────────────────────┘
```

**FileItem hover state:**
```
│  [📄 32px] Mi Presentación 2024.pptx     3.2 MB [✕←visible]│
│            ← fondo surface-secondary →               │
```

**Botón X:** Visible solo cuando el cursor está sobre el FileItem (group-hover). Al hacer hover sobre el X: color error.

**Footer layout:**
- Padding: 12px vertical, 16px horizontal
- "Añadir más archivos": ghost button con ícono `Plus` a la izquierda
- "Convertir →": primary button, 44px alto, a la derecha
- Entre ellos: flex gap

**Confirmación "Limpiar todo":**
- Si hay 1 o 2 archivos: acción inmediata sin confirmación.
- Si hay 3 o más: muestra `ConfirmDialog` antes de limpiar.

---

## 5. Estado `processing` — Conversión en curso

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ⟳ Convirtiendo archivos... — 1 de 3 completados   │ ← GlobalProgress h=44px
│  ───────────────────────────────────────────────────│
│                                                      │
│  [📄 24px] Mi Presentación 2024.pptx     ✓ Completado│ ← h=72px, opac 70%
│  ████████████████████████████████████ 100%          │ ← barra verde
│  ───────────────────────────────────────────────────│
│  [🎵 24px] grabacion_reunion.mp3       ⟳ Procesando │ ← h=72px, opac 100%
│  ██████████████░░░░░░░░░░░░░░░░░░░░░░  shimmer       │ ← barra shimmer
│  ───────────────────────────────────────────────────│
│  [📊 24px] presupuesto_q1.xlsx         ○ En espera  │ ← h=72px, opac 100%
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░              │ ← sin barra
│                                                      │
│  ───────────────────────────────────────────────────│
│                              [     Cancelar     ]    │ ← footer h=56px
└──────────────────────────────────────────────────────┘
```

**Importante:** El botón Cancelar es destructive secondary. Mientras `isCancelling === true`: el botón dice "Cancelando..." y está disabled con opacidad 0.4.

**ProcessingFileItem — estado error (si ocurre):**
```
│  [📄 24px] informe_protegido.pdf       ✗ Error       │
│  El archivo está protegido con contraseña             │ ← text-xs error
│  ████████████████████████████████████               │ ← barra roja
```

---

## 6. Estado `results` — Conversión completada (éxito total)

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │
├────────────────────┬─────────────────────────────────┤
│                    │                                 │
│ ✓ 3 archivos       │  ┌─ Toolbar ──────────────────┐│
│   convertidos      │  │ mi_presentacion_2024.md     ││ ← text-xs tertiary
│ ─────────────────  │  │            [Vista] [Crudo]  ││ ← toggle
│                    │  └─────────────────────────────┘│
│ ■ mi_presentacion_ │                                 │ ← activo (bg accent-subtle)
│ ○ grabacion_reun.. │  # Mi Presentación 2024         │ ← markdown renderizado
│ ○ presupuesto_q1.. │                                 │
│                    │  Este documento presenta los    │
│                    │  resultados del primer          │
│  ← sidebar 280px → │  trimestre...                  │
│                    │                                 │
│                    │  ## Agenda                      │
│                    │                                 │
│                    │  1. Introducción                │
│                    │  2. Resultados                  │
│                    │                                 │
├────────────────────┴─────────────────────────────────┤
│  [Nueva conversión]                   [Guardar ZIP ↓]│ ← footer h=56px
└──────────────────────────────────────────────────────┘
```

**Sidebar specs:**
- Ancho fijo: 280px
- Borde derecho: `1px solid var(--color-border)`
- Padding del resumen: 16px
- Ítem seleccionado: fondo `var(--color-accent-subtle)`, borde izquierdo 3px accent

**Ítem de archivo en sidebar:**
- Alto: 48px
- Ícono 20px + nombre truncado (1 línea) + badge ✓ o ✗
- Cursor: pointer para completed, default para error

**Preview panel specs:**
- Toolbar: 40px alto, fondo `var(--color-surface)`, borde inferior
- Contenido: padding 24px, scroll vertical independiente

**Footer specs:**
- "Nueva conversión": ghost button a la izquierda
- "Guardar ZIP" / "Guardar .md": primary button a la derecha
- Si `savedPath !== null`: añadir entre los dos: texto "Guardado ✓" + botón ghost "Mostrar en carpeta"

---

## 7. Estado `results` — Conversión con errores parciales

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │
├────────────────────┬─────────────────────────────────┤
│                    │                                 │
│ ✓ 2 de 3          │  [preview del archivo            │
│   convertidos      │   seleccionado]                 │
│ ✗ 1 con error      │                                 │
│ ─────────────────  │                                 │
│                    │                                 │
│ ✓ mi_presentac...  │                                 │
│ ✓ presupuesto_q... │                                 │
│ ✗ grabacion_reu... │                                 │
│   Audio muy corto  │  ← mensaje de error en sidebar  │
│                    │                                 │
├────────────────────┴─────────────────────────────────┤
│  [Nueva conv.] [Reintentar fallidos]  [Guardar ZIP ↓]│
└──────────────────────────────────────────────────────┘
```

**Ítem de error en sidebar:**
- Nombre con color `text-error`
- Mensaje de error en `text-xs text-error opacity-80` debajo del nombre
- No clickeable

---

## 8. Estado `results` — Todos fallaron

```
┌──────────────────────────────────────────────────────┐
│  [icon] Markify                         [🌙] │ [ES]  │
├────────────────────┬─────────────────────────────────┤
│                    │                                 │
│ ✗ 0 de 3          │                                 │
│   convertidos      │     [FileX 48px ícono]          │
│ ✗ 3 con error      │                                 │
│ ─────────────────  │  No se pudo convertir ningún    │
│                    │  archivo. Revisa los errores     │
│ ✗ archivo1...      │  en la lista.                   │
│   Error desc.      │                                 │
│ ✗ archivo2...      │                                 │
│   Error desc.      │                                 │
│ ✗ archivo3...      │                                 │
│   Error desc.      │                                 │
├────────────────────┴─────────────────────────────────┤
│  [Nueva conversión]          [Reintentar todos]      │
└──────────────────────────────────────────────────────┘
```

**Nota:** Cuando todos fallaron, NO mostrar el botón "Guardar ZIP". Solo "Nueva conversión" y "Reintentar todos" (que funciona igual que "Reintentar fallidos").

---

## 9. Modal — Descarga del modelo Whisper

```
┌──────────────────────────────────────────────────────┐
│  [overlay rgba(0,0,0,0.4) + blur 8px]               │
│                                                      │
│              ┌──────────────────────┐                │
│              │                      │  ← w=400px     │
│              │    [Brain 48px]      │                │
│              │                      │                │
│              │  Descarga requerida  │ ← text-xl bold │
│              │                      │                │
│              │  Para transcribir    │                │
│              │  audio necesitamos   │                │
│              │  descargar el modelo │                │
│              │  de IA (≈145 MB).   │ ← text-sm sec  │
│              │  Solo ocurre una vez.│                │
│              │                      │                │
│              │  [Cancelar][Descargar│                │
│              │            y cont. →]│                │
│              └──────────────────────┘                │
└──────────────────────────────────────────────────────┘
```

**Durante descarga (reemplaza botones):**
```
│              │  Descargando modelo...│                │
│              │  ███████░░░░  47%     │                │
│              │  68.3 MB de 145.0 MB  │                │
│              └──────────────────────┘                │
```

**Modal specs:**
- Ancho: max-w-[400px]
- Border radius: `var(--radius-xl)` = 20px
- Padding interno: 32px
- Sombra: `var(--shadow-modal)`
- Fondo: `var(--color-surface)`
- **Durante descarga:** no se puede cerrar con Escape ni click en overlay

**Animación de entrada del modal:**
- `scaleIn` (200ms spring): `scale(0.96) opacity(0)` → `scale(1) opacity(1)`

---

## 10. ConfirmDialog — Cancelar conversión

```
              ┌──────────────────────┐
              │                      │ ← w=360px
              │  ¿Cancelar          │ ← text-lg semibold
              │  conversión?        │
              │                      │
              │  Los archivos        │
              │  procesados hasta    │
              │  ahora se            │ ← text-sm secondary
              │  descartarán.        │
              │                      │
              │  [Continuar conv.][Sí│
              │                 cancel]│
              └──────────────────────┘
```

**Botones:** "Continuar convirtiendo" (secondary) a la izquierda, "Sí, cancelar" (destructive) a la derecha.

---

## 11. ConfirmDialog — Limpiar lista

```
              ┌──────────────────────┐
              │  ¿Limpiar la lista? │ ← text-lg semibold
              │                      │
              │  Se eliminarán los  │
              │  5 archivos de la   │ ← número dinámico
              │  lista.             │
              │                      │
              │     [Cancelar] [Limpiar]│
              └──────────────────────┘
```

---

## 12. Toast de errores de validación

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│                         ┌─────────────────────────┐  │
│                         │ ✗ Formato no compatible: │  │ ← esquina inferior derecha
│                         │   .xyz                  │  │
│                         │ ✗ El archivo supera el  │  │
│                         │   límite de 500 MB      │  │
│                         │                     [✕] │  │
│                         └─────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Toast specs:**
- Posición: bottom-right, 16px de margen
- Ancho: máximo 320px
- Border radius: `var(--radius-lg)`
- Fondo: `var(--color-surface-elevated)`
- Sombra: `var(--shadow-lg)`
- Borde izquierdo: 3px solid `var(--color-error)`
- Auto-dismiss: 5 segundos
- Animación entrada: `slideInUp` desde abajo
- Animación salida: fade out + slide down

---

## 13. Animaciones de transición entre estados

Todas las transiciones entre `appState` usan `AnimatePresence mode="wait"` en `App.tsx`.

| De → Hacia | Animación saliente | Animación entrante |
|-----------|-------------------|-------------------|
| `empty` → `files-ready` | fade out (150ms) | fade in + slide up 8px (200ms) |
| `files-ready` → `processing` | fade out (150ms) | fade in (200ms) |
| `processing` → `results` | fade out (150ms) | fade in + scale 0.98→1 (250ms spring) |
| `results` → `empty` | fade out (150ms) | fade in (200ms) |
| `files-ready` → `empty` | fade out (150ms) | fade in (200ms) |

**Implementación con Framer Motion:**
```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={appState}
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -4 }}
    transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
    className="h-full"
  >
    {/* Vista actual */}
  </motion.div>
</AnimatePresence>
```

---

## 14. Responsive — Comportamiento al redimensionar

La ventana tiene mínimos (800×600px) pero el usuario puede agrandarla libremente.

**Elementos que crecen con el ancho:**
- DropZone: crece hasta `max-w-[560px]` centrada — el resto es espacio vacío
- FileList: ocupa todo el ancho disponible
- ProcessingView: ocupa todo el ancho disponible
- ResultsView sidebar: **fijo en 280px** — el preview absorbe el espacio extra

**Elementos que crecen con el alto:**
- Lista de archivos (FileList, ProcessingView): el scroll area crece
- Preview panel: el área de scroll crece
- DropZone: permanece centrada verticalmente

**Breakpoint de layout del preview:**
- Si `width < 860px`: el sidebar se colapsa a 220px (solo iconos + badges, nombre truncado más agresivamente)
- Si `width < 800px`: imposible (mínimo de la ventana)

---

## 15. Accesibilidad

- Todos los botones tienen `aria-label` cuando no tienen texto visible (ThemeToggle, botón X de FileItem).
- Los estados de carga tienen `aria-live="polite"` en GlobalProgress para lectores de pantalla.
- El foco del teclado sigue el orden visual.
- Los modales atrapan el foco mientras están abiertos (`focus-trap`).
- El contraste de todos los textos cumple WCAG AA (mínimo 4.5:1).
- `prefers-reduced-motion` desactiva todas las animaciones (ver spec `02-design-system.md` § CSS).
