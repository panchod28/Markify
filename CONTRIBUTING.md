# Contributing to Markify

Welcome! Markify is a cross-platform desktop app that converts documents (PDF, PPTX, XLSX, DOCX, HTML, CSV) and audio/video (MP3, MP4, WAV, etc.) to Markdown. It's built with Tauri v2, React 18, TypeScript, Vite, and a Python sidecar.

We're glad you're here. Issues and pull requests in **Spanish or English** are equally welcome — write in whichever language you're most comfortable with.

---

## Code of Conduct

Be respectful, inclusive, and constructive. Harassment, insults, or discrimination of any kind will not be tolerated. We want this to be a space where everyone feels safe to contribute, ask questions, and learn.

---

## How to Report a Bug

1. **Check existing issues** to avoid duplicates.
2. **Open a new issue** on [GitHub Issues](https://github.com/panchod28/markify/issues).
3. Include the following information:
   - **Description** — what happened and what you expected.
   - **Steps to reproduce** — detailed enough that someone else can trigger the bug.
   - **Expected vs actual behavior**.
   - **OS and Markify version** (e.g., macOS 15.2, Markify 1.0.0).
   - **File type** that caused the issue (PDF, MP3, DOCX, etc.).
   - **Logs** if applicable (see below).

### Where to find logs

| OS | Location |
|----|----------|
| macOS | `~/Library/Logs/com.markify.desktop/` |
| Windows | `%APPDATA%\com.markify.desktop\logs\` |
| Linux | `~/.local/share/com.markify.desktop/logs/` |

You can also run the app from the terminal (`npm run tauri dev`) to see sidecar stderr output in real time.

---

## How to Suggest a Feature

1. **Open an issue** with the **enhancement** label.
2. Describe the **use case** — not just the solution. What problem are you trying to solve?
3. If you've seen something similar in another app, mention it as a reference point.
4. Consider whether the feature aligns with Markify's scope: offline-first, privacy-respecting, local conversion of documents and media to Markdown.

---

## Development Setup

### Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| **Node.js** | 20.19+ | Use [nvm](https://github.com/nvm-sh/nvm) or [fnm](https://github.com/Schniz/fnm) |
| **Rust** | latest stable | Install via [rustup](https://rustup.rs/) |
| **Python** | 3.12 | Required for the sidecar |
| **ffmpeg** | any recent | Must be on `PATH` (for audio/video conversion) |
| **Git** | any recent | |
| **Microsoft C++ Build Tools** | — | Windows only: required for Rust compilation |

#### Mac-specific prerequisites

```bash
# Install ffmpeg
brew install ffmpeg

# Verify
ffmpeg -version
node --version   # ≥ 20.19
rustc --version  # latest stable
python3.12 --version
```

#### Windows-specific prerequisites

```powershell
# Install Chocolatey (if not installed)
# https://chocolatey.org/install

# Install ffmpeg
choco install ffmpeg -y

# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# During installation, select: "Desktop development with C++"

# Verify
ffmpeg -version
node --version   # ≥ 20.19
rustc --version  # latest stable
python --version # 3.12
```

#### Linux-specific prerequisites

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y ffmpeg libwebkit2gtk-4.1-dev \
  build-essential curl wget file libxdo-dev libssl-dev \
  libayatana-appindicator3-dev librsvg2-dev

# Fedora
sudo dnf install -y ffmpeg webkit2gtk4.1-devel openssl-devel \
  libappindicator-gtk3-devel librsvg2-devel
```

### Clone & Install

```bash
git clone https://github.com/panchod28/markify.git
cd markify
npm install
```

### Python Sidecar Setup

The sidecar handles document conversion (markitdown), audio transcription (Whisper) and OCR for images and scanned PDFs (RapidOCR). It runs as a separate process communicating with the Tauri backend via JSON over stdin/stdout.

#### macOS / Linux

```bash
cd sidecar
python3 -m venv .venv
source .venv/bin/activate
pip install setuptools==70.0.0
pip install -r requirements.txt
python build.py
cd ..
```

#### Windows (PowerShell)

```powershell
cd sidecar
python -m venv .venv
.venv\Scripts\activate
pip install setuptools==70.0.0
pip install -r requirements.txt
python build.py
cd ..
```

> **markitdown is pinned** (`sidecar/requirements.txt`) because the OCR for DOCX/PPTX relies on two of its internals (`pre_process_docx` and the `<!-- Slide number: N -->` marker) and its output format changes between versions. To bump it, run `python -m pytest tests` (the no-regression tests compare against markitdown's own output) and the regression folder before changing the pin.

> **Note:** `build.py` compiles the sidecar with PyInstaller (`--onedir`) into the **folder** `src-tauri/binaries/markify-sidecar/` (the executable plus `_internal/`). `tauri dev` runs it from there and the installers bundle it. Re-run `npm run build:sidecar` after pulling changes to the sidecar; any older single-file `markify-sidecar-<target>` binary is no longer used and can be deleted.
>
> The first launch of a freshly built sidecar can take 30–50 s on macOS (one-time OS verification of the new files); later launches take about 2 s. You can check a build with `python smoke_test.py` from `sidecar/`.

### OCR and sidecar tests

The OCR code lives in `sidecar/ocr/` and is imported lazily: converting a document or audio file never loads OpenCV/ONNX. The pipeline decides **per PDF page** (`page_classifier.py`): all-text PDFs go through `convert_document` unchanged; if any page is scanned or mixed, `pdf_pipeline.convert_pdf` handles it page by page (a single `try/except` per page, cancel flag checked before each page, progress reported per page).

```bash
cd sidecar
pip install pytest reportlab        # reportlab only builds the test PDFs
python fetch_ocr_models.py           # downloads ocr/models/*.onnx (SHA-256 pinned); build.py also calls it
python -m pytest -q                  # everything, including the real OCR tests
python -m pytest -q -m "not ocr"     # fast loop: skips the tests that load the OCR engine
python tests/stress_pdf_memory.py 200   # 200-page scanned PDF: peak RSS (<= 1.5 GB), flat memory, cancel latency
python smoke_test.py                 # packaged build: CSV, scanned image and scanned PDF through the real binary
```

To check a platform you don't have (Windows), run the manual **OCR check** workflow from the Actions tab (`.github/workflows/ocr-check.yml`): tests, 60-page memory/time run, sidecar build, smoke test and size, on macOS and Windows. It publishes nothing.

Test PDFs are generated by `tests/make_fixtures.py` (nothing binary is committed). Real OCR tests assert a character error rate; the corpus is synthetic, so also check a few real scans by hand before a release.

**Images inside DOCX/PPTX** (`ocr/office_images.py`, routed by extension in `main.py` like `.pdf`): a file with no embedded images goes through `convert_document` unchanged. DOCX uses mammoth's image hook (text goes where the image was; sizes come from `wp:extent`, matched by SHA-1); PPTX swaps every picture for a text box at the same coordinates in an in-memory copy and lets markitdown convert it. Shared helpers: `ocr/image_loader.py` (load from path or bytes) and `ocr/recognize.py` (`read_simple`, `read_upright`). Fixtures: `tests/make_office_fixtures.py`; `tests/make_regression_folder.py <dir>` builds one file per accepted format (plus a DOCX and a PPTX with an image) for a manual run from the UI.

Tuning knobs live in one place each: `ocr/office_images.py` (`OFFICE_MIN_AREA`, `OFFICE_MIN_TEXT_CHARS`, pixel fallback — calibrated with real icons, photos and a real deck, see the change's design.md), `ocr/page_classifier.py` (`MIN_TEXT_CHARS`, `IMAGE_MIN_AREA`, `SCAN_COVERAGE`), `ocr/layout.py` (`MIN_CONFIDENCE`, column/paragraph thresholds), `ocr/pdf_pipeline.py` (`RENDER_DPI`, `MAX_SIDE_PX`) and `ocr/rapidocr_engine.py` (detection side limit; going back to RapidOCR's default raises peak RAM from ~1.1 GB to ~1.9 GB). To plug in another engine, add a class with `recognize(image) -> list[OcrLine]` and register it in `ocr/engine.py::ENGINES`.

### Whisper progress/cancel hook

`sidecar/whisper_progress.py` replaces `whisper.transcribe`'s internal `tqdm` while a transcription runs, so cancelling works between Whisper's ~30 s windows and progress is real. It depends on that internal detail, so `openai-whisper` is pinned in `sidecar/requirements.txt`. When you bump the version, run `python -m pytest tests` in `sidecar/`: `test_installed_whisper_exposes_the_hook_point` fails if the hook point moved (the sidecar itself falls back to the old behaviour with a warning on stderr instead of crashing).

### Run in Development

```bash
npm run dev
# or equivalently:
npm run tauri dev
```

This starts both the Vite dev server (frontend on `localhost:1420`) and the Tauri window with the Python sidecar attached.

### Build for Production

```bash
npm run tauri build
```

The output binaries will be in `src-tauri/target/release/bundle/`.

### Useful Commands

```bash
npm run lint          # Run ESLint
npm run type-check    # Run TypeScript type checking
npm run test          # Run Vitest tests
npm run test:watch    # Run tests in watch mode
```

---

## AI-Assisted Development

Markify was built with heavy assistance from AI coding tools. This section explains how the AI development workflow is set up so you can contribute efficiently — with or without AI assistance.

### Tools Used

- **[OpenCode](https://opencode.ai)** — AI coding agent used as the primary pair-programming assistant. It reads the codebase, edits files, runs commands, and follows project-specific rules.
- **[Claude by Anthropic](https://anthropic.com/claude)** — The AI model powering OpenCode. Claude Sonnet 4 or later is recommended for best results with this project's context and rules.

### Installing OpenCode

1. Follow the installation guide at [opencode.ai/docs](https://opencode.ai/docs).
2. Connect OpenCode to your Claude API key (Anthropic Console).
3. Open the Markify project in OpenCode; it will automatically read `CLAUDE.md` and the `openspec/specs/` directory for context.

### How AI Is Used in This Project

- OpenCode acts as the agent that reads files, edits code, and runs commands.
- Claude provides the reasoning, code generation, and instruction following.
- Prompts can be given in **Spanish or English** — the model handles both fluently.
- The `CLAUDE.md` file at the project root provides complete project context to the AI.
- The `openspec/specs/` directory contains 10 detailed specification files covering every aspect of the project.
- The `.opencode/commands/` directory contains reusable command shortcuts for common tasks.

### Key Rules When Using AI on This Project

These rules exist in `CLAUDE.md` and the spec files — any AI agent working on Markify must follow them. If you're writing code directly (without AI), these still apply.

1. **Python sidecar — NEVER write plain text to stdout.** The sidecar communicates with Rust exclusively via JSON newline-delimited messages using `write_message()`. Plain text to stdout will break the protocol.

2. **Always call `sys.stdout.flush()`** after every `write_message()`. Without flushing, the Rust backend may never receive the message.

3. **Never use `print()`** in any sidecar file. Use `sys.stderr` via `print(..., file=sys.stderr)` for debugging.

4. **TypeScript — always use `addFilePaths(paths)`** with absolute file paths when adding files to the conversion queue. Never use `addFiles()` with the browser File API — Tauri's file dialogs provide real file system paths.

5. **Tauri config — `beforeDevCommand` must be `"npm run vite"`**, not `"npm run dev"`. Using `"npm run dev"` causes an infinite loop because `npm run dev` calls `tauri dev` which calls the beforeDevCommand again.

6. **Tauri config — `beforeBuildCommand` must be `"npm run vite:build"`**, not `"npm run build"`. Same reason: `npm run build` calls `tauri build` creating a loop.

7. **Windows encoding** — stdout and stdin must be reconfigured to UTF-8 at the start of the sidecar with `sys.stdout.reconfigure(encoding='utf-8')` and `sys.stdin.reconfigure(encoding='utf-8')`.

8. **Cross-platform** — all code on the `main` branch must work on **both Mac and Windows**. Test on both platforms before opening a PR, or run CI to verify.

### Suggested Prompt Template for OpenCode

When starting a new OpenCode session on Markify, you can use this template to give it full context:

```
I'm working on the Markify project — a cross-platform desktop app built with
Tauri v2, React 18, TypeScript, and a Python sidecar that converts documents
and audio to Markdown.

Please read CLAUDE.md and openspec/specs/INDEX.md first for full project context.

[Describe your task here — e.g., "I need to add support for EPUB files"
or "The drop zone doesn't accept files dragged from Finder on macOS"]
```

---

## Project Structure

```
markify/
├── src/                      # Frontend React
│   ├── components/           # UI components organized by feature
│   │   ├── conversion/       # Processing view, file progress
│   │   ├── dropzone/         # Drag-and-drop file input
│   │   ├── files/            # File list and items
│   │   ├── layout/           # App shell, header, toggles
│   │   ├── modals/           # Dialogs and toasts
│   │   ├── results/          # Results view, sidebar, preview
│   │   └── ui/               # shadcn/ui primitives
│   ├── hooks/                # Custom React hooks
│   ├── i18n/                 # Internationalization (ES + EN)
│   ├── lib/                  # Utility functions
│   ├── stores/               # Zustand state management
│   ├── types/                # TypeScript type definitions
│   ├── App.tsx               # State-based routing with AnimatePresence
│   └── main.tsx              # Entry point
├── src-tauri/                # Tauri backend (Rust)
│   └── src/
│       ├── lib.rs            # Plugin registration, command handlers
│       ├── main.rs           # Entry point
│       └── commands/         # Tauri command implementations
├── sidecar/                  # Python sidecar
│   ├── main.py               # stdin/stdout event loop
│   ├── protocol.py           # JSON message read/write
│   ├── converter.py          # Document → Markdown (markitdown)
│   ├── ocr/                  # OCR: engine, layout, page classifier, image + PDF pipelines
│   ├── tests/                # pytest (fixtures generated by make_fixtures.py)
│   ├── whisper_handler.py    # Audio → Markdown (Whisper)
│   ├── model_manager.py      # Whisper model download
│   ├── error_messages.py     # Error translations (ES/EN)
│   └── requirements.txt      # Python dependencies
├── openspec/
│   └── specs/                # Detailed specification files
│       └── INDEX.md          # Start here for spec overview
├── .github/
│   └── workflows/            # CI/CD (Release on tag)
├── CLAUDE.md                 # AI assistant context (read by OpenCode)
└── CONTRIBUTING.md           # This file
```

### Before touching any module, read its spec

| # | Spec | Covers | Read before editing |
|---|------|--------|---------------------|
| 01 | `01-types.md` | TypeScript types, constants, supported extensions | Any `.ts` or `.tsx` file |
| 02 | `02-design-system.md` | CSS tokens, Tailwind config, shadcn/ui | Any UI component |
| 03 | `03-stores.md` | Zustand stores + Tauri event hooks | `src/stores/` |
| 04 | `04-tauri-commands.md` | Rust commands, sidecar state, events | `src-tauri/src/` |
| 05 | `05-sidecar-protocol.md` | Python sidecar protocol | `sidecar/` |
| 06 | `06-components.md` | React component specs, props, animations | `src/components/` |
| 07 | `07-screens.md` | Screen wireframes, state transitions | `src/App.tsx` |
| 08 | `08-i18n.md` | i18n config, message keys (ES/EN) | `src/i18n/` |
| 09 | `09-pipeline.md` | End-to-end pipeline, validation, cancellation | Conversion logic |
| 10 | `10-build.md` | Build process, PyInstaller, packaging | Build/distribution |

---

## Known risks to track as separate issues

Found while adding OCR; not fixed there on purpose:

- **Whisper model path when frozen** (`sidecar/model_manager.py::get_model_path`): in a packaged build it points next to the sidecar executable (inside the app bundle / install folder), not to a per-user writable data directory. It works while that folder is writable and breaks on read-only or per-machine installs.
- **First launch after install is slow** (30–50 s on macOS) because the OS verifies the new files once; the UI gives no hint during that wait.
- **No per-page timeout in OCR**: ONNX Runtime inference cannot be interrupted, so cancelling takes effect between pages, not inside one.
- **Mixed PDFs lose pdfplumber tables**: once a PDF has any scanned or mixed page, native-text pages are extracted with pdfminer per page, so table detection is lost on them. All-text PDFs are unchanged.
- **Whisper picks the audio language automatically** (`language=None`). It works with natural voices (Spanish clips from Mónica/Paulina were detected as `es` with probability 1.0); a robotic novelty voice (macOS "Eddy") was misdetected and garbled even when forcing `es`, so that was the audio, not the app. If users report misdetections, add an "audio language" option (Auto / Español / English) passed as `language=` to `model.transcribe`.
- **Images in Office files**: crops and rotations applied inside the document are ignored, DOCX headers/footers are not extracted, text of fewer than 6 letters/digits inside an image is dropped, and the alt text of small images is ignored on purpose (in a real deck it was stock-icon titles copied from the web).
- **OCR memory on Windows is unmeasured**; the ≤ 1.5 GB budget was measured on Apple Silicon only.

---

## Pull Request Guidelines

1. **Open an issue first** for bugs and features so we can discuss before you write code.
2. **Branch from `main`** using a descriptive name: `fix/dropzone-macos`, `feat/epub-support`, etc.
3. **Keep PRs focused** — one change per PR. Small PRs get merged faster.
4. **Follow existing code conventions:**
   - TypeScript types go in `src/types/index.ts`, not inline.
   - Use `cn()` from `src/lib/utils.ts` for conditional Tailwind classes.
   - Global state via Zustand stores — no `useState` for shared state.
   - Animations via Framer Motion `AnimatePresence` — see spec 06 and 07.
5. **Run checks before pushing:**
   ```bash
   npm run lint
   npm run type-check
   npm run test
   ```
6. **Test on both Mac and Windows** if your change touches platform-specific code (sidecar, file paths, encoding). If you can't test both, mention it in the PR and CI will verify.
7. **Update `openspec/specs/`** if your change modifies behavior covered by an existing spec.
8. **Write PR descriptions in Spanish or English** — whatever you prefer.

---

## Releasing

Before tagging a release, regenerate the third-party license texts in the build environment (they list the packages installed there) and check there is no unreviewed copyleft:

```bash
sidecar/.venv/bin/python scripts/gen_licenses.py --check
```

Releases are automated via GitHub Actions (`.github/workflows/release.yml`). Pushing a tag matching `v*` triggers the build pipeline:

```bash
git tag v1.1.0
git push origin v1.1.0
```

The CI pipeline:
1. Builds the Python sidecar with PyInstaller for macOS (Apple Silicon) and Windows (x86_64).
2. Compiles the Tauri app for each platform.
3. Creates a draft GitHub Release with `.dmg` (Mac) and `.msi`/`.exe` (Windows) installers.
