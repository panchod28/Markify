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

The sidecar handles document conversion (markitdown) and audio transcription (Whisper). It runs as a separate process communicating with the Tauri backend via JSON over stdin/stdout.

#### macOS / Linux

```bash
cd sidecar
python3 -m venv .venv
source .venv/bin/activate
pip install setuptools==70.0.0
pip install "markitdown[all] @ git+https://github.com/microsoft/markitdown.git#subdirectory=packages/markitdown"
pip install "numpy<2.4" openai-whisper torch PyInstaller
python build.py
cd ..
```

#### Windows (PowerShell)

```powershell
cd sidecar
python -m venv .venv
.venv\Scripts\activate
pip install setuptools==70.0.0
pip install "markitdown[all] @ git+https://github.com/microsoft/markitdown.git#subdirectory=packages/markitdown"
pip install "numpy<2.4" openai-whisper torch PyInstaller
python build.py
cd ..
```

> **Note:** `build.py` compiles the sidecar with PyInstaller into a single binary placed at `src-tauri/binaries/`. The Tauri build process expects it there.

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

Releases are automated via GitHub Actions (`.github/workflows/release.yml`). Pushing a tag matching `v*` triggers the build pipeline:

```bash
git tag v1.1.0
git push origin v1.1.0
```

The CI pipeline:
1. Builds the Python sidecar with PyInstaller for macOS (Apple Silicon) and Windows (x86_64).
2. Compiles the Tauri app for each platform.
3. Creates a draft GitHub Release with `.dmg` (Mac) and `.msi`/`.exe` (Windows) installers.
