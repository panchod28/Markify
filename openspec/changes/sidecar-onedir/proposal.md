## Why

El sidecar se empaqueta con PyInstaller `--onefile`: en **cada** arranque descomprime ~570 MB (torch, whisper, markitdown…) a un directorio temporal y macOS vuelve a verificar esas librerías recién escritas. Medido en macOS arm64 con el código actual: el binario actual tarda **41–46 s** en arrancar y responder, cada vez que se abre la app; compilado como `--onedir` tarda **25.7 s la primera vez** (verificación única de macOS) y **1.4 s las siguientes**. Con esos tiempos el comando `check_whisper_model` (timeout de 5 s) ya falla al abrir la app, y el change `add-ocr-image-pdf-support` empeoraría el arranque al añadir OpenCV (el `import cv2` congelado pasó de 0.1 s a ~15 s por la misma causa).

## What Changes

- `sidecar/build.py` produce una carpeta `--onedir` (`src-tauri/binaries/markify-sidecar/` con el ejecutable y `_internal/`) en lugar de un único archivo con triple.
- Tauri deja de usar `externalBin`: la carpeta se incluye como *resource* y `spawn_sidecar` resuelve el ejecutable desde el directorio de recursos y lo lanza con el mismo plugin shell. El protocolo stdin/stdout, `SidecarState`, los eventos y el resto de comandos **no cambian**.
- El workflow de release empaqueta/descarga la carpeta como `tar` (conserva permisos y symlinks), añade un *smoke test* del sidecar compilado (arranca y responde `check_model`) y mide el tiempo de arranque.
- `check_whisper_model` tolera el primer arranque lento (timeout 5 s → 60 s) y el frontend captura su error en lugar de dejarlo sin manejar.
- Documentación de build (README, CONTRIBUTING, spec `10-build`).

Sin cambios **BREAKING** para el usuario final. Para contribuidores: `npm run build:sidecar` genera una carpeta, no un archivo; hay que volver a ejecutarlo tras actualizar.

## Capabilities

### New Capabilities

- `sidecar-onedir-packaging`: forma del artefacto del sidecar (`--onedir`), reglas de `build.py`, empaquetado en CI, verificación del binario compilado y presupuesto de arranque.
- `sidecar-launch`: cómo la app localiza y lanza el sidecar empaquetado (producción y `tauri dev`), error claro si falta, y tolerancia al primer arranque lento.

### Modified Capabilities

<!-- Ninguna en formato OpenSpec: los specs vigentes son .md planos (04-tauri-commands, 05-sidecar-protocol, 10-build).
     Al archivar hay que reflejar las diferencias en 04 y 10 (ver tasks.md, grupo 6). -->

## Impact

- **Python**: `sidecar/build.py` (flags `--onedir`, destino, limpieza), sin cambios en módulos del sidecar.
- **Rust**: `src-tauri/src/commands/sidecar.rs` (`spawn_sidecar` y timeout de `check_whisper_model`); `src-tauri/tauri.conf.json` (`bundle.resources` en lugar de `bundle.externalBin`); `capabilities/default.json` sin cambios previstos (el lanzamiento es desde Rust, no desde el webview).
- **Frontend**: `useConversionStore.checkWhisperModel` (manejo de error).
- **CI**: `.github/workflows/release.yml` (artefacto tar, extracción, smoke test).
- **Tamaño**: instalado ocupa ~570 MB en disco (hoy ocupa ~240 MB instalado **más** ~570 MB temporales por ejecución, que además quedan huérfanos si el proceso muere); el instalador comprimido es comparable (tar.gz del sidecar: 180 MB frente a 238 MB del `--onefile`; el build de medición no incluyó python-pptx/openpyxl/xlrd, hay que reconfirmar con el build completo).
- **Relación con otros changes**: es prerrequisito de `add-ocr-image-pdf-support` (resuelve su Open Question 7).
