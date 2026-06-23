## ADDED Requirements

### Requirement: Command registration in lib.rs
The system SHALL register all 8 Tauri commands in `lib.rs` using `tauri::generate_handler![]` and initialize plugins: `tauri-plugin-shell`, `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-store`.

#### Scenario: App builder configuration
- **WHEN** the Tauri app is built
- **THEN** `.plugin()` calls SHALL register all 4 plugins and `.invoke_handler()` SHALL list all 8 commands

### Requirement: Sidecar spawn on setup
The system SHALL spawn the Python sidecar process during `setup()` using `app.shell().sidecar("markify-sidecar")` and store the `CommandChild` in managed state.

#### Scenario: App launches
- **WHEN** the app starts and `setup()` runs
- **THEN** the sidecar process SHALL be spawned and its handle SHALL be stored in `SidecarState`

### Requirement: SidecarState managed state
The system SHALL define a `SidecarState` struct with `pub child: Mutex<CommandChild>` and register it via `app.manage()`.

#### Scenario: Shared sidecar access
- **WHEN** a command needs to write to the sidecar
- **THEN** it SHALL access the child via `app.state::<SidecarState>()` and lock the Mutex

### Requirement: Cargo.toml dependencies
The system SHALL configure `Cargo.toml` with dependencies: `tauri` v2, `tauri-plugin-shell` v2, `tauri-plugin-dialog` v2, `tauri-plugin-fs` v2, `tauri-plugin-store` v2, `serde` v1, `serde_json` v1, `uuid` v1 with `v4` feature, `zip` v0.6, `tokio` v1 with `full` feature.

#### Scenario: Project compilation
- **WHEN** `cargo build` is executed
- **THEN** all dependencies SHALL resolve and compile successfully

### Requirement: Release profile optimization
The system SHALL configure release profile with `opt-level = 3`, `lto = true`, `codegen-units = 1`, `strip = true`.

#### Scenario: Release build
- **WHEN** building for production
- **THEN** the binary SHALL be optimized with LTO and stripped symbols

### Requirement: tauri.conf.json window configuration
The system SHALL configure `tauri.conf.json` with window dimensions 960×680 default, 800×600 minimum, centered, resizable, with decorations and shadow.

#### Scenario: App window opens
- **WHEN** the app launches
- **THEN** it SHALL open at 960×680 centered on screen

### Requirement: External bin configuration
The system SHALL declare `markify-sidecar` as an external binary in `bundle.externalBin` for bundling.

#### Scenario: Production build
- **WHEN** `tauri build` runs
- **THEN** the sidecar binary SHALL be included in the app bundle

### Requirement: Capabilities permissions
The system SHALL create `capabilities/default.json` with permissions: `core:default`, `shell:allow-open`, `shell:allow-spawn`, `dialog:allow-save`, `dialog:allow-open`, `fs:allow-write-text-file`, `fs:allow-read-text-file`, `store:default`.

#### Scenario: Command invocation
- **WHEN** the frontend calls `invoke('save_markdown', ...)`
- **THEN** the dialog and file write permissions SHALL be granted

### Requirement: CSP security policy
The system SHALL configure CSP as `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'` to allow Tailwind inline styles.

#### Scenario: Stylesheet loading
- **WHEN** the frontend loads Tailwind CSS with inline styles
- **THEN** the CSP SHALL allow it via `style-src 'unsafe-inline'`
