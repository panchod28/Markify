# Markify

**Convert anything to Markdown — locally, instantly, beautifully.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-orange.svg)](https://github.com/panchod28/markify/releases)
[![Platform: macOS](https://img.shields.io/badge/macOS-Apple%20Silicon%20%7C%20Intel-lightgrey.svg)](#)
[![Platform: Windows](https://img.shields.io/badge/Windows-10%2F11%20x86__64-lightgrey.svg)](#)
[![Tauri: v2](https://img.shields.io/badge/Tauri-v2-ffc131.svg)](https://tauri.app)

A cross-platform desktop app that converts documents (PDF, DOCX, PPTX, XLSX, CSV, EPUB, HTML) and audio/video (MP3, MP4, WAV, M4A) into clean Markdown — using local AI. Everything runs on your machine. No cloud, no accounts, no limits.

---

## Why Markify?

- **100% local** — All processing happens on your device. Your files never leave your computer.
- **Audio transcription with Whisper AI** — Transcribe MP3, MP4, WAV, and more into structured Markdown using OpenAI's Whisper model running locally.
- **Cross-platform** — Native experience on macOS (Apple Silicon + Intel) and Windows 10/11.
- **Multiple formats, one tool** — PDFs, spreadsheets, presentations, ebooks, HTML, audio, video — drop them all at once and get clean Markdown.
- **Beautiful dark/light UI** — Thoughtfully designed interface that respects your system theme.

---

## Features

### Supported Formats

| Category | Formats | Engine |
|----------|---------|--------|
| **Documents** | PDF, DOCX, PPTX, XLSX, CSV, EPUB, HTML | markitdown (+ OCR for scanned PDF pages) |
| **Images** | PNG, JPG, JPEG, WEBP, BMP, TIF, TIFF | Local OCR (RapidOCR, PP-OCRv5) |
| **Audio** | MP3, WAV, M4A, OGG, FLAC, WMA, AAC | Whisper (base) |
| **Video** | MP4, MOV, AVI, MKV, WebM, WMV, FLV | Whisper (base) |

### Key Capabilities

- Drag & drop multiple files at once
- Batch conversion with real-time progress per file
- Live Markdown preview with rendered/raw toggle
- Large file preview with smart truncation (50k chars)
- Automatic filename sanitization for cross-OS compatibility
- Local OCR for images and scanned PDFs (Spanish and English), 100 % offline — the models ship inside the installer
- PDFs are analysed page by page: text pages are extracted as before, scanned pages (and figures with text) are recognized, rotated pages are straightened, and two-column layouts are read column by column
- A page that cannot be read never fails the whole file: it is replaced by a `<!-- Markify: page N could not be processed -->` comment and the file shows a warning icon
- Cancel conversions mid-flight
- Retry failed files individually
- Export results as individual `.md` files or a single `.zip`
- System language detection (English / Spanish)

---

## Download

> Markify is in **public beta**. Expect frequent updates and improvements.

Download the latest version from [GitHub Releases](https://github.com/panchod28/markify/releases):

| Platform | Format |
|----------|--------|
| macOS (Apple Silicon) | `.dmg` |
| macOS (Intel) | `.dmg` |
| Windows 10/11 (x86_64) | `.msi` / `.exe` |

---

## Development Setup

### Prerequisites (both platforms)

- **Node.js** 20.19+
- **Rust** ([rustup](https://rustup.rs))
- **Python** 3.12
- **ffmpeg** in PATH

### macOS

```bash
# 1. Install system dependencies
brew install ffmpeg

# 2. Clone and install frontend dependencies
git clone https://github.com/panchod28/markify.git
cd markify
npm install

# 3. Set up Python sidecar
cd sidecar
python3.12 -m venv .venv
source .venv/bin/activate
pip install setuptools==70.0.0
pip install "markitdown[all] @ git+https://github.com/microsoft/markitdown.git#subdirectory=packages/markitdown"
pip install -r requirements.txt
python build.py   # also downloads the OCR models (needs internet once, SHA-256 verified)
cd ..

# 4. Launch dev mode
npm run dev
```

### Windows

```powershell
# 1. Install Microsoft C++ Build Tools
#    https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 2. Install ffmpeg (via winget or manual download)
winget install ffmpeg

# 3. Clone and install frontend dependencies
git clone https://github.com/panchod28/markify.git
cd markify
npm install

# 4. Set up Python sidecar
cd sidecar
python -m venv .venv
.venv\Scripts\activate
pip install setuptools==70.0.0
pip install "markitdown[all] @ git+https://github.com/microsoft/markitdown.git#subdirectory=packages/markitdown"
pip install -r requirements.txt
python build.py   # also downloads the OCR models (needs internet once, SHA-256 verified)
cd ..

# 5. Launch dev mode
npm run dev
```

---

## How It Works

```
┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐
│  Drag & Drop │ ───▶ │  Python Sidecar  │ ───▶ │  Preview & Save  │
│  your files  │      │  (stdin/stdout)  │      │  your Markdown   │
└──────────────┘      └─────────────────┘      └──────────────────┘
```

1. **Drag & Drop** — Drop any supported file into the window. Markify validates formats, sizes, and handles duplicates intelligently.

2. **Python sidecar converts** — Tauri spawns a Python sidecar process that communicates via JSON over stdin/stdout. Documents go through [markitdown](https://github.com/microsoft/markitdown); audio/video through [OpenAI Whisper](https://github.com/openai/whisper); images and scanned PDF pages through a local OCR engine ([RapidOCR](https://github.com/RapidAI/RapidOCR) on ONNX Runtime, CPU only).

3. **Preview and save** — Browse converted results in a sidebar, preview rendered Markdown in real time, and export as individual `.md` files or a single `.zip`.

### OCR limits

- Languages: Spanish and English (the Latin model also reads other Latin-script languages, but they are not tested).
- Text only: tables, headings and handwriting are not reconstructed. Lines below the confidence threshold are dropped and reported as a warning instead of emitting noise.
- Multi-frame TIFFs: only the first frame is read (a warning says how many were skipped). Password-protected PDFs are rejected; Markify does not ask for the password.
- Size and speed: OCR adds about 100 MB to the installer. Expect roughly 0.3–1.5 s per scanned page on Apple Silicon; the 1st launch after install is slower while the OS verifies the new files.

### Architecture

```
React 18 (Vite)  ←→  Tauri v2 (Rust)  ←→  Python sidecar (PyInstaller)
     UI                IPC layer              Conversion engine
```

---

## Project Structure

```
markify/
├── src/                        # React frontend
│   ├── components/             # UI components
│   │   ├── conversion/         # Processing views
│   │   ├── dropzone/           # File drop area
│   │   ├── files/              # File list & icons
│   │   ├── layout/             # App shell, header
│   │   ├── modals/             # Dialogs & toasts
│   │   ├── results/            # Results sidebar & preview
│   │   └── ui/                 # shadcn/ui primitives
│   ├── stores/                 # Zustand state management
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities & helpers
│   └── types/                  # TypeScript type definitions
├── src-tauri/                  # Tauri backend (Rust)
│   ├── src/                    # Rust command handlers
│   └── binaries/               # Compiled sidecar folder (PyInstaller --onedir)
├── sidecar/                    # Python conversion engine
│   ├── main.py                 # Entry point & message loop
│   ├── converter.py            # Document → Markdown
│   ├── ocr/                    # Local OCR: engine, layout, image and PDF pipelines
│   ├── fetch_ocr_models.py     # Downloads the OCR models (build time only, SHA-256 checked)
│   ├── whisper_handler.py      # Audio → Transcription
│   ├── model_manager.py        # Whisper model downloader
│   ├── protocol.py             # JSON stdin/stdout protocol
│   ├── error_messages.py       # i18n error strings (ES/EN)
│   └── build.py                # PyInstaller packager
└── .github/workflows/          # CI/CD pipelines
```

---

## Contributing

Markify is open source and welcomes contributions! Issues and pull requests in English or Spanish are both fine.

- **Report bugs** — Found something broken? [Open an issue](https://github.com/panchod28/markify/issues) with steps to reproduce.
- **Suggest features** — Have an idea to make Markify better? Let's discuss it.
- **Submit PRs** — Fork the repo, create a branch, and open a pull request. Check the [development setup](#development-setup) to get started.
- **Feedback** — General thoughts, UX suggestions, or docs improvements are always welcome.

---

## License

MIT © 2026 [Juan David Rengifo](https://github.com/panchod28)

---

Built with by [Juan David Rengifo](https://github.com/panchod28)
