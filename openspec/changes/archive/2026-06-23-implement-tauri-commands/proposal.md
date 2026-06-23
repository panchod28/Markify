## Why

Markify necesita el backend Rust que orqueste: spawn del sidecar Python, envío/recepción de comandos via stdin/stdout, emisión de eventos al frontend, diálogos nativos de archivo, creación de ZIP y operaciones de sistema. Los stores (spec 03) ya invocan estos comandos via `tauriCommands`, pero los comandos Rust aún no existen. Sin este backend, la app no puede ejecutar conversiones.

## What Changes

- Crear `src-tauri/src/commands/` con 4 módulos Rust: `mod.rs`, `conversion.rs`, `file_system.rs`, `sidecar.rs`
- Implementar 8 comandos Tauri: `start_conversion`, `cancel_conversion`, `save_markdown`, `save_zip`, `open_in_folder`, `check_whisper_model`, `download_whisper_model`, `get_app_version`
- Implementar spawn del sidecar Python y loop de lectura de stdout con traducción a eventos Tauri
- Implementar `SidecarState` con `Mutex<CommandChild>` para comunicación bidireccional
- Actualizar `lib.rs` con registro de comandos, plugins y setup
- Actualizar `Cargo.toml` con dependencias: `tauri-plugin-shell`, `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-store`, `serde`, `serde_json`, `uuid`, `zip`, `tokio`
- Configurar `tauri.conf.json` con dimensiones de ventana, bundle y permisos CSP
- Crear `capabilities/default.json` con permisos Tauri v2

## Capabilities

### New Capabilities

- `rust-backend`: Estructura del backend Rust — lib.rs, Cargo.toml, tauri.conf.json, capabilities
- `conversion-cmds`: Comandos de conversión (`start_conversion`, `cancel_conversion`) que escriben al sidecar vía stdin
- `file-system-cmds`: Comandos de sistema de archivos (`save_markdown`, `save_zip`, `open_in_folder`) con diálogos nativos
- `sidecar-management`: Gestión del proceso Python — spawn, stdout loop, traducción de mensajes a eventos, estado compartido

### Modified Capabilities

N/A — proyecto greenfield, sin backend Rust existente que modificar.

## Impact

- **Crea**: `src-tauri/src/commands/mod.rs`, `conversion.rs`, `file_system.rs`, `sidecar.rs`
- **Modifica**: `src-tauri/src/lib.rs`, `src-tauri/src/main.rs`, `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`, `src-tauri/capabilities/default.json`
- **Dependencias Rust nuevas**: `tauri-plugin-shell`, `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-store`, `zip`, `uuid`
- **Dependencias Rust existentes**: `tauri` v2, `serde`, `serde_json`, `tokio`
- **Sidecar**: Requiere que el binario `markify-sidecar` exista en `src-tauri/binaries/` (creado por spec 10-build)
