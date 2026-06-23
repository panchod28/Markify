## 1. Sidecar Build Script

- [x] 1.1 Create `sidecar/build.py` — PyInstaller build with platform detection, `--onefile`, `--console`, module exclusions

## 2. Build Configuration

- [x] 2.1 Update `vite.config.ts` — already configured correctly with `@` alias, port 1420, strict port, watch ignore
- [x] 2.2 Update `package.json` — added scripts (`dev`, `build`, `build:sidecar`, `build:all`, `lint`, `type-check`, `test`) and version 1.0.0

## 3. Sidecar Tests

- [x] 3.1 Create `sidecar/tests/test_sanitizer.py` — 9 parametrized pytest cases
- [x] 3.2 Create `sidecar/tests/test_protocol.py` — write_message and read_message tests with mock stdout/stdin

## 4. Verification

- [x] 4.1 Run `npx tsc --noEmit` — zero errors
- [x] 4.2 Python syntax verified for all test files and build.py
