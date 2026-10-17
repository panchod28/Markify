# Spec 10 — Build & Packaging
> Markify — Proceso completo de build, empaquetado del sidecar, distribución por plataforma y estructura del proyecto.

---

## 1. Estructura completa del proyecto

```
markify/
│
├── package.json                  ← Scripts NPM y dependencias del frontend
├── vite.config.ts                ← Config de Vite
├── tsconfig.json                 ← TypeScript config
├── tailwind.config.ts            ← Tailwind config (ver spec 02)
├── components.json               ← shadcn/ui config (ver spec 02)
├── .gitignore
│
├── src/                          ← Frontend React
│   ├── main.tsx                  ← Entry point — importa i18n, renderiza App
│   ├── App.tsx                   ← Router de estados + modales globales
│   ├── index.css                 ← Design tokens CSS (ver spec 02)
│   │
│   ├── components/
│   │   ├── ui/                   ← Componentes shadcn/ui (auto-generados con CLI)
│   │   │   ├── button.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   └── tooltip.tsx
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── LanguageToggle.tsx
│   │   ├── dropzone/
│   │   │   ├── DropZone.tsx
│   │   │   └── DropZoneCompact.tsx
│   │   ├── files/
│   │   │   ├── FileList.tsx
│   │   │   └── FileItem.tsx
│   │   ├── conversion/
│   │   │   ├── ProcessingView.tsx
│   │   │   ├── ProcessingFileItem.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── GlobalProgress.tsx
│   │   ├── results/
│   │   │   ├── ResultsView.tsx
│   │   │   ├── ResultsSidebar.tsx
│   │   │   ├── ResultFileItem.tsx
│   │   │   ├── PreviewPanel.tsx
│   │   │   └── ResultsActionBar.tsx
│   │   └── modals/
│   │       ├── WhisperModelModal.tsx
│   │       ├── ConfirmDialog.tsx
│   │       └── ValidationErrorToast.tsx
│   │
│   ├── stores/
│   │   ├── useAppStore.ts
│   │   ├── useConversionStore.ts
│   │   └── usePreviewStore.ts
│   │
│   ├── hooks/
│   │   ├── useTauriEvents.ts
│   │   ├── useSystemTheme.ts
│   │   └── useFileValidation.ts
│   │
│   ├── lib/
│   │   ├── cn.ts                 ← Helper clsx + tailwind-merge
│   │   ├── tauri.ts              ← Wrappers tipados invoke/listen
│   │   ├── sanitizer.ts          ← sanitizeFilename() TypeScript
│   │   ├── fileUtils.ts          ← getExtension, getFileCategory, etc.
│   │   └── formatters.ts         ← formatFileSize, generateZipName
│   │
│   ├── types/
│   │   └── index.ts              ← Todos los tipos (ver spec 01)
│   │
│   └── i18n/
│       ├── index.ts              ← Config i18next (ver spec 08)
│       └── locales/
│           ├── en/
│           │   ├── common.json
│           │   └── messages.json
│           └── es/
│               ├── common.json
│               └── messages.json
│
├── src-tauri/                    ← Backend Rust / Tauri
│   ├── Cargo.toml
│   ├── Cargo.lock
│   ├── tauri.conf.json
│   ├── capabilities/
│   │   └── default.json
│   ├── build.rs                  ← Script de build de Tauri (no modificar)
│   ├── icons/                    ← Iconos de la app (generar con tauri icon)
│   │   ├── 32x32.png
│   │   ├── 128x128.png
│   │   ├── 128x128@2x.png
│   │   ├── icon.icns             ← macOS
│   │   └── icon.ico              ← Windows
│   ├── binaries/                 ← Salida de build.py (ignorada por git)
│   │   └── markify-sidecar/      ← PyInstaller --onedir
│   │       ├── markify-sidecar[.exe]
│   │       └── _internal/        ← librerías y datos
│   ├── tauri.macos.conf.json     ← bundle.macOS.files → Resources/sidecar
│   ├── tauri.windows.conf.json   ← bundle.resources → sidecar/
│   └── src/
│       ├── main.rs
│       ├── lib.rs
│       └── commands/
│           ├── mod.rs
│           ├── conversion.rs
│           ├── file_system.rs
│           └── sidecar.rs
│
└── sidecar/                      ← Python sidecar
    ├── main.py
    ├── protocol.py
    ├── converter.py
    ├── whisper_handler.py
    ├── model_manager.py
    ├── sanitizer.py
    ├── error_messages.py
    ├── requirements.txt
    ├── build.py                  ← Script de build PyInstaller
    └── tests/
        ├── test_sanitizer.py
        ├── test_converter.py
        ├── test_protocol.py
        └── fixtures/
            ├── sample.pdf
            ├── sample.docx
            ├── sample.xlsx
            ├── sample.pptx
            ├── sample.mp3
            ├── empty.pdf
            └── corrupted.docx
```

---

## 2. `package.json` — Scripts y dependencias

```json
{
  "name": "markify",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev":            "tauri dev",
    "build":          "tauri build",
    "build:sidecar":  "cd sidecar && python build.py",
    "build:all":      "npm run build:sidecar && npm run build",
    "preview":        "vite preview",
    "lint":           "eslint src --ext .ts,.tsx --report-unused-disable-directives",
    "type-check":     "tsc --noEmit",
    "test":           "vitest run",
    "test:watch":     "vitest",
    "shadcn:add":     "npx shadcn@latest add"
  },
  "dependencies": {
    "@tauri-apps/api":                 "^2",
    "@tauri-apps/plugin-dialog":       "^2",
    "@tauri-apps/plugin-fs":           "^2",
    "@tauri-apps/plugin-shell":        "^2",
    "@tauri-apps/plugin-store":        "^2",
    "clsx":                            "^2.1.0",
    "framer-motion":                   "^11.0.0",
    "i18next":                         "^23.0.0",
    "i18next-browser-languagedetector":"^8.0.0",
    "lucide-react":                    "^0.400.0",
    "react":                           "^18.3.0",
    "react-dom":                       "^18.3.0",
    "react-dropzone":                  "^14.2.0",
    "react-i18next":                   "^14.0.0",
    "react-markdown":                  "^9.0.0",
    "remark-gfm":                      "^4.0.0",
    "tailwind-merge":                  "^2.2.0",
    "zustand":                         "^4.5.0"
  },
  "devDependencies": {
    "@tauri-apps/cli":                 "^2",
    "@types/react":                    "^18.3.0",
    "@types/react-dom":                "^18.3.0",
    "@typescript-eslint/eslint-plugin":"^7.0.0",
    "@typescript-eslint/parser":       "^7.0.0",
    "@vitejs/plugin-react":            "^4.3.0",
    "autoprefixer":                    "^10.4.0",
    "eslint":                          "^8.57.0",
    "postcss":                         "^8.4.0",
    "tailwindcss":                     "^3.4.0",
    "typescript":                      "^5.4.0",
    "vite":                            "^5.0.0",
    "vitest":                          "^1.6.0"
  }
}
```

---

## 3. `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(async () => ({
  plugins: [react()],

  // El dev server de Vite escucha en el puerto que Tauri espera
  server: {
    port: 1420,
    strictPort: true,
    // Requerido para Tauri — no usar localhost con HTTPS
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },

  // Alias para imports absolutos con @/
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
}));
```

---

## 4. `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## 5. Build del Python Sidecar (`sidecar/build.py`)

> Actualizado por el change `sidecar-onedir`. El código vigente es `sidecar/build.py`; aquí solo se fijan las reglas.

- PyInstaller en modo **`--onedir`** (no `--onefile`): el `--onefile` re-extraía ~570 MB en cada arranque (41–50 s en macOS); con `--onedir` el primer arranque es lento una sola vez y los siguientes tardan ≈ 2 s.
- Salida fija: `src-tauri/binaries/markify-sidecar/` (ejecutable + `_internal/`), sin target triple en el nombre. Cada plataforma compila la suya; el triple solo se usa para nombrar el artefacto de CI.
- `build.py` borra la salida anterior antes de compilar.
- Flags relevantes: `--collect-submodules numpy._core --collect-submodules numpy.lib` (numpy ≥ 2), `--collect-all magika/markitdown/PIL/pptx`, `--copy-metadata …`, `--collect-data whisper`, y la ruta `setuptools/_vendor` cuando existe `jaraco` (setuptools ≥ 71).
- OCR: `build.py` llama a `fetch_ocr_models.py` (modelos con SHA-256 fijado; un hash distinto rompe el build) y añade `--add-data <sidecar/ocr/models>:ocr/models`, `--collect-all rapidocr` (con `--exclude-module rapidocr.inference_engine.pytorch`), `--collect-binaries onnxruntime`; después borra los modelos PP-OCRv6 que arrastra el wheel de rapidocr y no se usan. Las importaciones de OCR son perezosas, así que el arranque en frío no cambia.
- Verificación: `cd sidecar && python smoke_test.py` (protocolo JSON puro, conversión de un CSV, de una imagen, de un PDF escaneado, de un DOCX y de un PPTX con una imagen por OCR, y arranque posterior ≤ 3 s). CI lo ejecuta antes de empaquetar.
- Tests: `python -m pytest tests -q` (incluye los tests con OCR real, marcados `ocr`). CI instala `pytest` y `reportlab` (genera los PDFs de prueba) y ejecuta `fetch_ocr_models.py` antes. Medidas locales (Apple Silicon): `python tests/stress_pdf_memory.py 200` → RSS pico ≈ 1.1 GB y plano, ≈ 0.3 s/página.
- Licencias: `THIRD_PARTY_NOTICES.md` y `THIRD_PARTY_LICENSES.txt` (textos completos, generado con `python sidecar/gen_licenses.py`) se incluyen en el instalador (`Resources/` en macOS vía `tauri.macos.conf.json`, junto al sidecar en Windows vía `tauri.windows.conf.json`). Actualizarlo al añadir o cambiar dependencias de OCR.

---

## 6. `sidecar/requirements.txt`

```
# Conversión de documentos (versión fijada: el OCR de DOCX/PPTX depende de sus internos)
markitdown[all]==0.1.6

# Transcripción de audio (Whisper local)
openai-whisper

# PyTorch — SOLO CPU (sin CUDA) para reducir tamaño y compatibilidad
# Instalar así: pip install torch==2.3.1+cpu --find-links https://download.pytorch.org/whl/torch_stable.html
torch==2.3.1+cpu
torchaudio==2.3.1+cpu

# Empaquetado
PyInstaller==6.8.0
```

**Comando de instalación para desarrollo:**
```bash
pip install "markitdown[all]==0.1.6" openai-whisper PyInstaller
pip install torch==2.3.1+cpu torchaudio==2.3.1+cpu \
  --find-links https://download.pytorch.org/whl/torch_stable.html
```

---

## 7. Proceso de build completo por plataforma

### 7.1 macOS (Intel y Apple Silicon)

```bash
# 1. Instalar Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 2. Instalar Python 3.11
brew install python@3.11

# 3. Instalar dependencias del proyecto
npm install
pip3.11 install -r sidecar/requirements.txt \
  torch==2.3.1+cpu --find-links https://download.pytorch.org/whl/torch_stable.html

# 4. Compilar el sidecar Python
npm run build:sidecar
# → Genera: src-tauri/binaries/markify-sidecar/ (carpeta --onedir)

# 5. Compilar la app Tauri
npm run build
# → Genera: src-tauri/target/release/bundle/dmg/Markify_1.0.0_x64.dmg
```

### 7.2 Windows

```powershell
# 1. Instalar Rust (desde https://rustup.rs)
# 2. Instalar Python 3.11 (desde python.org)
# 3. Instalar Visual Studio Build Tools con C++ workload

# 4. En PowerShell (admin no requerido):
npm install
pip install -r sidecar/requirements.txt
pip install torch==2.3.1+cpu --find-links https://download.pytorch.org/whl/torch_stable.html

# 5. Compilar
npm run build:sidecar
npm run build
# → Genera: src-tauri/target/release/bundle/nsis/Markify_1.0.0_x64-setup.exe
#         y: src-tauri/target/release/bundle/msi/Markify_1.0.0_x64_en-US.msi
```

### 7.3 Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependencias del sistema
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev build-essential curl wget file \
  libssl-dev libayatana-appindicator3-dev librsvg2-dev \
  python3.11 python3.11-pip

# 2. Instalar Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 3. Instalar dependencias del proyecto
npm install
python3.11 -m pip install -r sidecar/requirements.txt \
  torch==2.3.1+cpu --find-links https://download.pytorch.org/whl/torch_stable.html

# 4. Compilar
npm run build:sidecar
npm run build
# → Genera: src-tauri/target/release/bundle/appimage/Markify_1.0.0_amd64.AppImage
#         y: src-tauri/target/release/bundle/deb/Markify_1.0.0_amd64.deb
```

---

## 8. Generación de iconos

Tauri requiere iconos en múltiples tamaños. Generar desde un PNG de 1024×1024:

```bash
# Con la CLI de Tauri (requiere tener la app inicializada):
npx tauri icon path/to/icon-1024.png
# → Genera automáticamente todos los tamaños en src-tauri/icons/
```

**Requisitos del ícono de Markify:**
- Fondo: color sólido (no transparente) para Windows ICO
- Bordes redondeados: radio ~22% del tamaño (estilo macOS)
- Debe verse bien en 16×16px (favicon de Windows)
- Paleta: usar el color de acento `#007AFF` como color principal

---

## 9. Cómo se incluye el sidecar en la app

`tauri.conf.json` **ya no** usa `bundle.externalBin`. La carpeta se incluye según la plataforma y se lanza desde Rust por ruta (`app.shell().command(ruta)`):

| Contexto | Configuración | Ruta |
|---|---|---|
| macOS instalado | `tauri.macos.conf.json`: `bundle.macOS.files = {"Resources/sidecar": "binaries/markify-sidecar"}` (conserva los symlinks; `bundle.resources` los desreferencia y añade ~280 MB) | `Contents/Resources/sidecar/markify-sidecar` |
| Windows instalado | `tauri.windows.conf.json`: `bundle.resources = {"binaries/markify-sidecar/": "sidecar/"}` | `<recursos>/sidecar/markify-sidecar.exe` |
| `tauri dev` | nada (no se copia) | `src-tauri/binaries/markify-sidecar/…` vía `CARGO_MANIFEST_DIR` |

---

## 10. Artifacts de distribución por plataforma

| Plataforma | Archivo generado | Ruta |
|------------|-----------------|------|
| macOS | `Markify_1.0.0_x64.dmg` | `src-tauri/target/release/bundle/dmg/` |
| macOS ARM | `Markify_1.0.0_aarch64.dmg` | `src-tauri/target/release/bundle/dmg/` |
| Windows | `Markify_1.0.0_x64-setup.exe` | `src-tauri/target/release/bundle/nsis/` |
| Windows | `Markify_1.0.0_x64_en-US.msi` | `src-tauri/target/release/bundle/msi/` |
| Linux | `Markify_1.0.0_amd64.AppImage` | `src-tauri/target/release/bundle/appimage/` |
| Linux | `Markify_1.0.0_amd64.deb` | `src-tauri/target/release/bundle/deb/` |

---

## 11. Tamaños estimados del bundle

| Componente | Tamaño aproximado |
|------------|------------------|
| Tauri runtime + WebView | ~3-5 MB |
| Frontend compilado (React + assets) | ~2-4 MB |
| Python sidecar (sin modelo Whisper) | ~80-120 MB |
| OCR (OpenCV, ONNX Runtime, shapely, modelos PP-OCRv5 ≈ 12.7 MB) | +~105 MB en disco (954 MB frente a 850 MB de la carpeta del sidecar sin OCR, medido en macOS) |
| **Instalador total (sin modelo)** | **~90-130 MB** |
| Modelo Whisper base (descarga on-demand) | ~145 MB |
| **Instalación total en disco** | **~250-300 MB** |

---

## 12. Instrucciones de primera ejecución para el usuario

### macOS — Incluir en el DMG como `LÉEME.txt`

```
MARKIFY — Instrucciones de instalación

1. Arrastra Markify a la carpeta Aplicaciones.

2. La primera vez que abras Markify, macOS mostrará un aviso
   de "desarrollador no identificado".

3. Para abrirla:
   - Clic derecho (o Control+Clic) sobre el ícono de Markify
   - Selecciona "Abrir"
   - En el diálogo que aparece, haz clic en "Abrir"

   Después de este paso, Markify se abrirá normalmente siempre.

4. Si el aviso no aparece o no puedes abrirla:
   - Ve a Ajustes del Sistema → Privacidad y Seguridad
   - Busca "Markify" y haz clic en "Abrir de todas formas"
```

### Windows — Mostrar en pantalla durante instalación o como README

```
MARKIFY — Instrucciones de instalación

1. Ejecuta el instalador Markify_Setup.exe.

2. Windows puede mostrar el aviso "Windows protegió tu PC"
   (SmartScreen).

3. Para continuar:
   - Haz clic en "Más información"
   - Luego haz clic en "Ejecutar de todas formas"

4. Completa la instalación normalmente.

   Después de instalada, Markify se abrirá sin advertencias.
```

---

## 13. Variables de entorno para desarrollo

```bash
# .env.development (no commitear)
# No se necesitan variables de entorno para v1
# El sidecar se detecta automáticamente por Tauri
```

---

## 14. Tests del sidecar (`sidecar/tests/`)

### `test_sanitizer.py`
```python
import pytest
from sanitizer import sanitize_filename

@pytest.mark.parametrize("original,expected", [
    ("Mi Presentación 2024.pptx",    "mi_presentacion_2024.md"),
    ("Reporte Anual (Final).pdf",    "reporte_anual_final.md"),
    ("audio grabación #3.mp3",       "audio_grabacion_3.md"),
    ("!@#$%.xlsx",                   "archivo_sin_nombre.md"),
    ("MAYÚSCULAS.pdf",               "mayusculas.md"),
    ("file.with.dots.pdf",           "file_with_dots.md"),
    ("123.pdf",                      "123.md"),
    ("   espacios   .pdf",           "espacios.md"),
    ("___guiones___.pdf",            "guiones.md"),
])
def test_sanitize_filename(original, expected):
    assert sanitize_filename(original) == expected
```

### `test_protocol.py`
```python
import json
import io
import sys
from unittest.mock import patch
from protocol import read_message, write_message

def test_write_message():
    """Verifica que write_message escribe JSON + newline y hace flush."""
    fake_stdout = io.StringIO()
    with patch("sys.stdout", fake_stdout):
        write_message({"type": "test", "payload": {}})
    output = fake_stdout.getvalue()
    assert output.endswith("\n")
    parsed = json.loads(output.strip())
    assert parsed["type"] == "test"

def test_read_message():
    """Verifica que read_message parsea JSON correctamente."""
    fake_input = '{"command": "convert", "payload": {}}\n'
    with patch("sys.stdin", io.StringIO(fake_input)):
        msg = read_message()
    assert msg["command"] == "convert"
```

---

## 15. Checklist pre-release

Verificar manualmente antes de cada build de distribución:

- [ ] `npm run type-check` pasa sin errores
- [ ] `npm run lint` pasa sin errores
- [ ] `npm run test` pasa todos los tests
- [ ] Sidecar compilado para la plataforma objetivo (carpeta `src-tauri/binaries/markify-sidecar/` existe y `python sidecar/smoke_test.py` pasa)
- [ ] `npm run build` completa sin errores
- [ ] El instalador generado funciona en una máquina limpia (sin Node, Python, ni Rust instalados)
- [ ] Drag & drop de PDF funciona y descarga el .md correctamente
- [ ] Drag & drop de MP3 funciona (descarga modelo si es necesario) y descarga el .md
- [ ] Un DOCX y un PPTX con una captura con texto salen con el texto de la imagen en su sitio y sin líneas `![..](..)`; un `.doc` o `.ppt` se rechaza con el mensaje de formato antiguo
- [ ] Una imagen PNG/JPG (ES y EN) y un PDF escaneado se convierten sin red; las tildes, ñ, ¿ y ¡ salen bien
- [ ] Un PDF con páginas ilegibles termina con aviso (icono + tooltip) y el resto de páginas convertidas
- [ ] Múltiples archivos generan ZIP correcto
- [ ] Cancelación funciona sin corromper el estado
- [ ] Cambio de tema light/dark funciona y persiste
- [ ] Cambio de idioma ES/EN funciona y persiste
- [ ] "Mostrar en carpeta" abre el Finder/Explorer en la ubicación correcta
- [ ] El aviso de seguridad del OS aparece y se puede superar con los pasos del LÉEME
