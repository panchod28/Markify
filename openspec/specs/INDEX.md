# Markify — OpenSpec Index

> Usa este índice para saber qué spec leer antes de implementar cualquier módulo.

| # | Spec | Cubre | Leer antes de tocar |
|---|------|-------|---------------------|
| 01 | `01-types.md` | Todos los TypeScript types, constantes, extensiones soportadas | Cualquier archivo `.ts` o `.tsx` |
| 02 | `02-design-system.md` | CSS custom properties, Tailwind config, shadcn/ui, keyframes, colores | Cualquier componente de UI |
| 03 | `03-stores.md` | Zustand stores completos (AppStore, ConversionStore, PreviewStore) + hook useTauriEvents | `src/stores/` |
| 04 | `04-tauri-commands.md` | Comandos Rust, SidecarState, manejo de eventos, Cargo.toml | `src-tauri/src/` |
| 05 | `05-sidecar-protocol.md` | Python sidecar completo: main.py, protocol.py, converter.py, whisper_handler.py | `sidecar/` |
| 06 | `06-components.md` | 23 componentes React con props, lógica y animaciones | `src/components/` |
| 07 | `07-screens.md` | Wireframes de las 6 pantallas, transiciones de estado, tamaños de ventana | `src/App.tsx`, layouts |
| 08 | `08-i18n.md` | Configuración i18next, JSONs ES/EN completos, reglas de pluralización | `src/i18n/` |
| 09 | `09-pipeline.md` | Pipeline end-to-end, validaciones, sanitización, cancelación | Lógica de conversión completa |
| 10 | `10-build.md` | Árbol de archivos, package.json exacto, PyInstaller, build Mac/Win/Linux | Empaquetado y distribución |

## Orden de implementación recomendado

```
01 types → 02 design-system → 03 stores → 08 i18n → 06 components → 07 screens → 04 tauri-commands → 05 sidecar-protocol → 09 pipeline → 10 build
```

## Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS v3 + shadcn/ui + Framer Motion + Zustand
- **Backend:** Tauri v2 (Rust)
- **Sidecar:** Python 3.11 + markitdown + openai-whisper (modelo `base`) + PyInstaller
- **i18n:** react-i18next (ES + EN)
- **Ventana:** 960×680 default, 800×600 mínimo
