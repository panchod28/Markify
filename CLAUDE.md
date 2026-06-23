# Markify — Contexto para opencode

## Qué es este proyecto
App de escritorio cross-platform (Mac, Windows, Linux) que convierte documentos (PDF, PPTX, XLSX, DOCX, HTML, CSV) y audio/video (MP3, MP4, WAV, etc.) a Markdown. Usa Tauri v2 + React 18 + Python sidecar.

## Stack exacto
| Capa | Tecnología | Versión |
|------|-----------|---------|
| Framework desktop | Tauri | v2 |
| Frontend | React + TypeScript + Vite | 18 / 5 / 5 |
| UI | Tailwind CSS + shadcn/ui | v3 |
| Animaciones | Framer Motion | 11 |
| Estado | Zustand | 4 |
| i18n | react-i18next | 15 |
| Backend Python | markitdown + openai-whisper | latest / base model |
| Empaquetado Python | PyInstaller | 6 |

## Estructura de carpetas
```
markify/
├── src/                      # Frontend React
│   ├── components/
│   │   ├── conversion/       # ProcessingView, ProcessingFileItem, GlobalProgress
│   │   ├── dropzone/         # DropZone, DropZoneCompact
│   │   ├── files/            # FileItem, FileList, FileIcon
│   │   ├── layout/           # AppShell, Header, ThemeToggle, LanguageToggle
│   │   ├── modals/           # WhisperModelModal, ConfirmDialog, ValidationErrorToast
│   │   ├── results/          # ResultsView, ResultsSidebar, ResultFileItem, PreviewPanel, ResultsActionBar
│   │   └── ui/               # shadcn/ui components
│   ├── hooks/                # useTauriEvents
│   ├── i18n/                 # index.ts + locales/es/ + locales/en/
│   ├── lib/                  # utils.ts (cn helper)
│   ├── stores/               # useAppStore, useConversionStore, usePreviewStore
│   ├── types/                # index.ts con todos los tipos TypeScript
│   ├── App.tsx               # Router de estados con AnimatePresence
│   └── main.tsx              # Entry point
├── src-tauri/                # Backend Rust
│   └── src/
│       ├── lib.rs            # Comandos Tauri + SidecarState
│       └── main.rs           # Entry point
├── sidecar/                  # Python sidecar
│   ├── main.py               # Loop stdin/stdout
│   ├── protocol.py           # read_message / write_message
│   ├── converter.py          # MarkItDown wrapper
│   ├── whisper_handler.py    # Transcripción con cancel_flag
│   ├── model_manager.py      # Descarga modelo Whisper
│   ├── error_messages.py     # Mensajes ES/EN
│   └── requirements.txt
└── openspec/
    └── specs/                # Las 10 specs del proyecto (leer antes de implementar)
        ├── INDEX.md          # ← LEER PRIMERO
        ├── 01-types.md
        ├── 02-design-system.md
        ├── 03-stores.md
        ├── 04-tauri-commands.md
        ├── 05-sidecar-protocol.md
        ├── 06-components.md
        ├── 07-screens.md
        ├── 08-i18n.md
        ├── 09-pipeline.md
        └── 10-build.md

```

## Reglas críticas — NUNCA violar

### Python sidecar
- **NUNCA escribir texto plano a stdout** — solo JSON newline-delimited via `write_message()`
- **Siempre hacer `sys.stdout.flush()`** después de cada `write_message()`
- **No usar `print()`** en ningún archivo del sidecar (usa `sys.stderr` para debug)
- El sidecar se comunica SOLO por stdin/stdout con Rust via `CommandChild`

### TypeScript / React
- Todos los tipos en `src/types/index.ts` — no crear tipos inline en componentes
- Usar `cn()` de `src/lib/utils.ts` para clases condicionales de Tailwind
- Estado global SOLO via Zustand stores — no `useState` para estado compartido
- Animaciones con Framer Motion `AnimatePresence` — ver spec 06 y 07

### Tauri
- Comandos Rust en `src-tauri/src/lib.rs`
- SidecarState usa `Mutex<Option<CommandChild>>`
- Eventos hacia el frontend: `conversion://progress`, `conversion://complete`, `conversion://error`, `conversion://cancelled`

### Diseño
- Color accent: `#007AFF` (light) / `#0A84FF` (dark)
- Ventana: 960×680 default, 800×600 mínimo
- Header macOS: padding-left 76px para los semáforos
- Tema via atributo `data-theme` en `<html>`
- Grid de 8px para todos los espaciados

## Orden de implementación recomendado
```
01 types → 02 design-system → 03 stores → 08 i18n → 06 components → 07 screens → 04 tauri-commands → 05 sidecar-protocol → 09 pipeline → 10 build
```

## Comandos útiles
```bash
# Desarrollo
npm run tauri dev

# Build producción
npm run tauri build

# Python sidecar (desarrollo)
cd sidecar && python main.py

# Build sidecar con PyInstaller
cd sidecar && python build.py
```

## Specs disponibles
Antes de implementar cualquier módulo, leer la spec correspondiente en `openspec/specs/`.
Ver `openspec/specs/INDEX.md` para el mapa completo.
