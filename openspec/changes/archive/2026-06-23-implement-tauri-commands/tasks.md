## 1. Cargo Configuration

- [x] 1.1 Update `src-tauri/Cargo.toml` with all dependencies (tauri v2, plugins: shell/dialog/fs/store, serde, serde_json, uuid with v4, zip 0.6, tokio) and release profile
- [x] 1.2 Verify `cargo check` passes with the new dependencies

## 2. Tauri Configuration

- [x] 2.1 Update `src-tauri/tauri.conf.json` with window dimensions (960x680 default, 800x600 min), bundle config, CSP, and external bin for sidecar
- [x] 2.2 Create/update `src-tauri/capabilities/default.json` with all required permissions

## 3. Sidecar Module

- [x] 3.1 Create `src-tauri/src/commands/sidecar.rs` with `SidecarState` struct, `spawn_sidecar()`, and `write_to_sidecar()` helper
- [x] 3.2 Implement `handle_sidecar_output()` — parse JSON lines and route by `type` field to corresponding Tauri events
- [x] 3.3 Implement `check_whisper_model` command using oneshot channel with 5s timeout
- [x] 3.4 Implement `download_whisper_model` command (fire-and-forget)
- [x] 3.5 Implement `get_app_version` command returning `CARGO_PKG_VERSION`

## 4. Conversion Commands

- [x] 4.1 Create `src-tauri/src/commands/conversion.rs` with `FilePayload` struct
- [x] 4.2 Implement `start_conversion` — build JSON with UUID, command "convert", files + lang payload, write to sidecar
- [x] 4.3 Implement `cancel_conversion` — send cancel JSON to sidecar

## 5. File System Commands

- [x] 5.1 Create `src-tauri/src/commands/file_system.rs` with `ZipFileEntry` struct
- [x] 5.2 Implement `save_markdown` — native save dialog with .md filter, write content, return path or null
- [x] 5.3 Implement `save_zip` — native save dialog with .zip filter, create ZIP in memory with Deflated compression, write to disk
- [x] 5.4 Implement `open_in_folder` with platform-specific implementations (macOS `open -R`, Windows `explorer /select`, Linux `xdg-open`)

## 6. Module Organization

- [x] 6.1 Create `src-tauri/src/commands/mod.rs` re-exporting all command modules
- [x] 6.2 Update `src-tauri/src/lib.rs` with plugin registration, command handler, and setup hook calling `spawn_sidecar`

## 7. Verification

- [x] 7.1 Run `cargo check` to verify all Rust code compiles without errors
