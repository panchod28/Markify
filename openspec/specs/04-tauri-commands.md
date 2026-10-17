# Spec 04 — Tauri Commands & Events API
> Markify — Contrato completo entre el frontend React y el backend Rust.
> Archivos destino: `src-tauri/src/commands/`, `src-tauri/src/lib.rs`
> Dependencias de tipos: spec `01-types.md`, spec `05-sidecar-protocol.md`

---

## 1. Estructura del lado Rust

```
src-tauri/src/
├── main.rs           ← Entry point (solo arrancar la app)
├── lib.rs            ← Builder de la app + registro de comandos + setup de plugins
└── commands/
    ├── mod.rs        ← Re-exporta todos los módulos
    ├── conversion.rs ← start_conversion, cancel_conversion
    ├── file_system.rs← save_markdown, save_zip, open_in_folder
    └── sidecar.rs    ← Gestión del proceso Python (spawn, stdin/stdout)
```

---

## 2. `lib.rs` — Registro de comandos y plugins

```rust
// src-tauri/src/lib.rs

use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            // Conversión
            commands::conversion::start_conversion,
            commands::conversion::cancel_conversion,
            // Sistema de archivos
            commands::file_system::save_markdown,
            commands::file_system::save_zip,
            commands::file_system::open_in_folder,
            // Sidecar / modelo
            commands::sidecar::check_whisper_model,
            commands::sidecar::download_whisper_model,
            commands::sidecar::get_app_version,
        ])
        .setup(|app| {
            // Spawnear el sidecar Python al arrancar la app
            commands::sidecar::spawn_sidecar(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error al iniciar Markify");
}
```

---

## 3. Comandos — Conversión (`commands/conversion.rs`)

### `start_conversion`

**Frontend llama:**
```typescript
invoke('start_conversion', {
  files: [{ id: string, path: string, category: 'document' | 'audio' }],
  lang: 'es' | 'en'
})
// Retorna: Promise<void>
// La respuesta real llega por eventos, no por el return value.
```

**Rust hace:**
1. Obtiene handle del sidecar (iniciado en setup).
2. Construye el mensaje JSON según el protocolo de spec 05.
3. Escribe el mensaje al stdin del sidecar con `\n` al final.
4. Retorna `Ok(())` inmediatamente — no espera respuesta.
5. El loop de lectura de stdout (ver `sidecar.rs`) procesa las respuestas.

```rust
#[tauri::command]
pub async fn start_conversion(
    app: tauri::AppHandle,
    files: Vec<FilePayload>,
    lang: String,
) -> Result<(), String> {
    // FilePayload = { id: String, path: String, category: String }
    let message = serde_json::json!({
        "id": uuid::Uuid::new_v4().to_string(),
        "command": "convert",
        "payload": {
            "files": files,
            "lang": lang
        }
    });
    write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error enviando al sidecar: {}", e))
}
```

---

### `cancel_conversion`

**Frontend llama:**
```typescript
invoke('cancel_conversion')
// Retorna: Promise<void>
```

**Rust hace:**
1. Escribe `{ "id": "...", "command": "cancel", "payload": {} }` al stdin del sidecar.
2. Retorna `Ok(())`.
3. El sidecar responde con `{ "type": "conversion_cancelled" }` en stdout.
4. El loop de stdout emite el evento `'conversion:cancelled'` al frontend.

```rust
#[tauri::command]
pub async fn cancel_conversion(app: tauri::AppHandle) -> Result<(), String> {
    let message = serde_json::json!({
        "id": uuid::Uuid::new_v4().to_string(),
        "command": "cancel",
        "payload": {}
    });
    write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error cancelando: {}", e))
}
```

---

## 4. Comandos — Sistema de archivos (`commands/file_system.rs`)

### `save_markdown`

**Frontend llama:**
```typescript
invoke('save_markdown', {
  content: string,       // Contenido markdown completo
  suggestedName: string  // "mi_archivo.md"
})
// Retorna: Promise<string | null>
// string = ruta absoluta donde se guardó
// null   = usuario canceló el diálogo
```

**Rust hace:**
1. Abre el diálogo nativo "Guardar como" con `tauri_plugin_dialog`.
2. Filtro del diálogo: `{ name: "Markdown", extensions: ["md"] }`.
3. Nombre sugerido: `suggestedName`.
4. Si el usuario cancela → retorna `null`.
5. Si confirma → escribe el contenido al path elegido con `tauri_plugin_fs`.
6. Retorna el path absoluto como `String`.

```rust
#[tauri::command]
pub async fn save_markdown(
    app: tauri::AppHandle,
    content: String,
    suggested_name: String,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let path = app.dialog()
        .file()
        .set_file_name(&suggested_name)
        .add_filter("Markdown", &["md"])
        .blocking_save_file();

    match path {
        Some(p) => {
            let path_str = p.to_string_lossy().to_string();
            std::fs::write(&path_str, content)
                .map_err(|e| format!("Error guardando archivo: {}", e))?;
            Ok(Some(path_str))
        }
        None => Ok(None), // Usuario canceló
    }
}
```

---

### `save_zip`

**Frontend llama:**
```typescript
invoke('save_zip', {
  files: [{ name: string, content: string }], // name = sanitizedName (.md)
  suggestedName: string  // "conversion_2026-06-22_14-30.zip"
})
// Retorna: Promise<string | null>
```

**Rust hace:**
1. Abre diálogo "Guardar como" con filtro `{ name: "ZIP", extensions: ["zip"] }`.
2. Si el usuario cancela → `null`.
3. Crea el ZIP en memoria usando la crate `zip`.
4. Para cada archivo en `files`: añade una entrada al ZIP con `name` y `content` (UTF-8).
5. Escribe el ZIP al path elegido.
6. Retorna el path.

```rust
// Dependencias en Cargo.toml:
// zip = "0.6"

#[tauri::command]
pub async fn save_zip(
    app: tauri::AppHandle,
    files: Vec<ZipFileEntry>,  // { name: String, content: String }
    suggested_name: String,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    use std::io::Write;
    use zip::write::FileOptions;

    let path = app.dialog()
        .file()
        .set_file_name(&suggested_name)
        .add_filter("ZIP", &["zip"])
        .blocking_save_file();

    match path {
        Some(p) => {
            let path_str = p.to_string_lossy().to_string();
            let file = std::fs::File::create(&path_str)
                .map_err(|e| format!("Error creando ZIP: {}", e))?;
            let mut zip = zip::ZipWriter::new(file);
            let options = FileOptions::default()
                .compression_method(zip::CompressionMethod::Deflated);

            for entry in &files {
                zip.start_file(&entry.name, options)
                    .map_err(|e| format!("Error añadiendo archivo al ZIP: {}", e))?;
                zip.write_all(entry.content.as_bytes())
                    .map_err(|e| format!("Error escribiendo contenido: {}", e))?;
            }

            zip.finish().map_err(|e| format!("Error finalizando ZIP: {}", e))?;
            Ok(Some(path_str))
        }
        None => Ok(None),
    }
}
```

---

### `open_in_folder`

**Frontend llama:**
```typescript
invoke('open_in_folder', { filePath: string })
// Retorna: Promise<void>
```

**Rust hace:**
- Abre el Finder (Mac), Explorer (Windows) o Nautilus (Linux) en la carpeta del archivo, con el archivo seleccionado.
- En Mac: `open -R /path/to/file`
- En Windows: `explorer /select,C:\path\to\file`
- En Linux: `xdg-open /path/to/folder`

```rust
#[tauri::command]
pub async fn open_in_folder(file_path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    std::process::Command::new("open")
        .args(["-R", &file_path])
        .spawn()
        .map_err(|e| e.to_string())?;

    #[cfg(target_os = "windows")]
    std::process::Command::new("explorer")
        .arg(format!("/select,{}", file_path))
        .spawn()
        .map_err(|e| e.to_string())?;

    #[cfg(target_os = "linux")]
    {
        let folder = std::path::Path::new(&file_path)
            .parent()
            .unwrap_or(std::path::Path::new("/"))
            .to_string_lossy()
            .to_string();
        std::process::Command::new("xdg-open")
            .arg(&folder)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}
```

---

## 5. Comandos — Sidecar y modelo (`commands/sidecar.rs`)

### `spawn_sidecar` (llamado en setup, no es un comando invoke)

```rust
// Se llama en lib.rs setup(), no desde el frontend.
// Spawna el proceso Python y arranca el loop de lectura de stdout.

// Tiempo máximo de check_whisper_model: el primer arranque en macOS puede tardar ~30-50 s.
const CHECK_MODEL_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(60);

pub fn spawn_sidecar(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    use tauri_plugin_shell::ShellExt;

    // El sidecar es una carpeta PyInstaller --onedir (ver spec 10, §9): se lanza por ruta,
    // no con `.sidecar()`. `sidecar_path()` resuelve dev (src-tauri/binaries) o instalada (recursos).
    let path = sidecar_path(app)?;
    let sidecar_command = app.shell().command(path);

    let (mut rx, child) = sidecar_command.spawn()?;

    // Guardar el child en el estado de la app para escribirle después
    app.manage(SidecarState { child: Mutex::new(child) });

    // Loop asíncrono para leer stdout
    let app_handle = app.handle().clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    handle_sidecar_output(&app_handle, &line).await;
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    eprintln!("[Sidecar stderr] {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Error(e) => {
                    eprintln!("[Sidecar error] {}", e);
                }
                tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                    eprintln!("[Sidecar] Terminado con status: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
    });

    Ok(())
}
```

### `handle_sidecar_output` — Traducir mensajes del sidecar a eventos Tauri

```rust
// Parsea cada línea JSON del sidecar y emite el evento Tauri correspondiente.
// Ver spec 05 para el protocolo completo de mensajes.

async fn handle_sidecar_output(app: &tauri::AppHandle, line: &[u8]) {
    let text = match String::from_utf8(line.to_vec()) {
        Ok(s) => s.trim().to_string(),
        Err(_) => return,
    };

    if text.is_empty() { return; }

    let msg: serde_json::Value = match serde_json::from_str(&text) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("[Sidecar] JSON inválido: {} — {}", e, text);
            return;
        }
    };

    match msg["type"].as_str() {
        Some("file_progress") | Some("file_result") => {
            // Emitir evento al frontend con el payload completo
            let _ = app.emit("conversion:file-update", &msg["payload"]);
        }
        Some("conversion_complete") => {
            let _ = app.emit("conversion:complete", ());
        }
        Some("conversion_cancelled") => {
            let _ = app.emit("conversion:cancelled", ());
        }
        Some("model_progress") => {
            let _ = app.emit("model:download-progress", &msg["payload"]);
        }
        Some("model_ready") => {
            let _ = app.emit("model:download-complete", ());
        }
        Some("model_error") => {
            let _ = app.emit("model:download-error", &msg["payload"]);
        }
        Some("model_status") => {
            // Respuesta al comando check_whisper_model
            // Resolver la oneshot channel pendiente (ver check_whisper_model)
        }
        other => {
            eprintln!("[Sidecar] Tipo de mensaje desconocido: {:?}", other);
        }
    }
}
```

---

### `check_whisper_model`

**Frontend llama:**
```typescript
invoke('check_whisper_model')
// Retorna: Promise<boolean>
```

**Rust hace:**
1. Escribe `{ "command": "check_model", "payload": {} }` al stdin del sidecar.
2. Espera la respuesta `{ "type": "model_status", "payload": { "available": bool } }` del stdout.
3. Retorna el valor de `available`.

> **Implementación:** Usar un `tokio::sync::oneshot` channel. El handler de stdout lo resuelve al recibir `model_status`.

```rust
#[tauri::command]
pub async fn check_whisper_model(app: tauri::AppHandle) -> Result<bool, String> {
    // Crear oneshot channel y guardarlo en AppState
    // Escribir al sidecar
    // Awaitar el channel (timeout de 5s)
    // Retornar el valor
    // (Implementación completa en el código fuente)
    todo!()
}
```

---

### `download_whisper_model`

**Frontend llama:**
```typescript
invoke('download_whisper_model')
// Retorna: Promise<void>
// El progreso llega por eventos 'model:download-progress' y 'model:download-complete'
```

**Rust hace:**
1. Escribe `{ "command": "download_model", "payload": {} }` al stdin.
2. Retorna `Ok(())`.
3. El sidecar descarga el modelo y emite `model_progress` y `model_ready` en stdout.

```rust
#[tauri::command]
pub async fn download_whisper_model(app: tauri::AppHandle) -> Result<(), String> {
    let message = serde_json::json!({
        "id": uuid::Uuid::new_v4().to_string(),
        "command": "download_model",
        "payload": {}
    });
    write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error: {}", e))
}
```

---

### `get_app_version`

**Frontend llama:**
```typescript
invoke('get_app_version')
// Retorna: Promise<string>  — Ejemplo: "1.0.0"
```

```rust
#[tauri::command]
pub fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
```

---

### `write_to_sidecar` — Helper interno

```rust
// Helper que escribe una línea JSON al stdin del sidecar.
// Siempre añade \n al final (protocolo newline-delimited JSON).

async fn write_to_sidecar(
    app: &tauri::AppHandle,
    message: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let state = app.state::<SidecarState>();
    let mut child = state.child.lock().await;
    let line = format!("{}\n", message);
    child.write(line.as_bytes()).await?;
    Ok(())
}
```

---

## 6. Estado del sidecar (AppState de Tauri)

```rust
// Estructura que se registra con app.manage() en setup()

use tokio::sync::Mutex;
use tauri_plugin_shell::process::CommandChild;

pub struct SidecarState {
    pub child: Mutex<CommandChild>,
}
```

---

## 7. `Cargo.toml` — Dependencias

```toml
[package]
name = "markify"
version = "1.0.0"
edition = "2021"

[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
tauri-plugin-dialog = "2"
tauri-plugin-fs = "2"
tauri-plugin-store = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4"] }
zip = "0.6"
tokio = { version = "1", features = ["full"] }

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
```

---

## 8. `tauri.conf.json` — Permisos y configuración

```json
{
  "productName": "Markify",
  "version": "1.0.0",
  "identifier": "com.markify.app",
  "app": {
    "withGlobalTauri": false,
    "windows": [
      {
        "title": "Markify",
        "width": 960,
        "height": 680,
        "minWidth": 800,
        "minHeight": 600,
        "center": true,
        "resizable": true,
        "decorations": true,
        "transparent": false,
        "shadow": true
      }
    ],
    "security": {
      "csp": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

---

## 9. `capabilities/default.json` — Permisos Tauri v2

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Permisos por defecto de Markify",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open",
    "shell:allow-spawn",
    "dialog:allow-save",
    "dialog:allow-open",
    "fs:allow-write-text-file",
    "fs:allow-read-text-file",
    "store:default"
  ]
}
```

---

## 10. Tabla resumen de comandos

| Comando | Parámetros | Retorno | Async |
|---------|-----------|---------|-------|
| `start_conversion` | `files[]`, `lang` | `void` | Sí |
| `cancel_conversion` | — | `void` | Sí |
| `save_markdown` | `content`, `suggestedName` | `string \| null` | Sí |
| `save_zip` | `files[]`, `suggestedName` | `string \| null` | Sí |
| `open_in_folder` | `filePath` | `void` | Sí |
| `check_whisper_model` | — | `boolean` | Sí |
| `download_whisper_model` | — | `void` | Sí |
| `get_app_version` | — | `string` | No |

## 11. Tabla resumen de eventos

| Evento | Payload | Disparado por |
|--------|---------|--------------|
| `conversion:file-update` | `ConversionProgressEvent` | Cada línea del sidecar (file_progress, file_result) |
| `conversion:complete` | — | Mensaje `conversion_complete` del sidecar |
| `conversion:cancelled` | — | Mensaje `conversion_cancelled` del sidecar |
| `model:download-progress` | `ModelDownloadProgressEvent` | Mensaje `model_progress` del sidecar |
| `model:download-complete` | — | Mensaje `model_ready` del sidecar |
| `model:download-error` | `{ message: string }` | Mensaje `model_error` del sidecar |
