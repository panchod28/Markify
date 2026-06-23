use std::collections::HashMap;
use std::sync::Arc;
use tauri::Emitter;
use tauri::Manager;
use tokio::sync::{Mutex, oneshot};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use uuid::Uuid;

pub struct SidecarState {
    pub child: Mutex<CommandChild>,
}

pub struct PendingCheck {
    pub tx: oneshot::Sender<bool>,
}

pub fn spawn_sidecar(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let sidecar_command = app.shell()
        .sidecar("markify-sidecar")
        .map_err(|e| format!("Sidecar no encontrado: {}", e))?;

    let (mut rx, child) = sidecar_command.spawn()?;

    app.manage(SidecarState { child: Mutex::new(child) });
    app.manage(Arc::new(Mutex::new(HashMap::<String, PendingCheck>::new())));

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
            if let Some(request_id) = msg["request_id"].as_str() {
                let state = app.state::<Arc<Mutex<HashMap<String, PendingCheck>>>>();
                let mut pending = state.lock().await;
                if let Some(check) = pending.remove(request_id) {
                    let available = msg["payload"]["available"].as_bool().unwrap_or(false);
                    let _ = check.tx.send(available);
                }
            }
        }
        other => {
            eprintln!("[Sidecar] Tipo de mensaje desconocido: {:?}", other);
        }
    }
}

pub async fn write_to_sidecar(
    app: &tauri::AppHandle,
    message: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let state = app.state::<SidecarState>();
    let mut child = state.child.lock().await;
    let line = format!("{}\n", message);
    child.write(line.as_bytes())?;
    Ok(())
}

#[tauri::command]
pub async fn check_whisper_model(app: tauri::AppHandle) -> Result<bool, String> {
    let request_id = Uuid::new_v4().to_string();

    let (tx, rx) = oneshot::channel::<bool>();
    let pending = PendingCheck { tx };

    {
        let state = app.state::<Arc<Mutex<HashMap<String, PendingCheck>>>>();
        let mut map = state.lock().await;
        map.insert(request_id.clone(), pending);
    }

    let message = serde_json::json!({
        "id": request_id,
        "command": "check_model",
        "payload": {}
    });

    write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error: {}", e))?;

    match tokio::time::timeout(std::time::Duration::from_secs(5), rx).await {
        Ok(Ok(available)) => Ok(available),
        Ok(Err(_)) => Err("Error interno en la comunicación".to_string()),
        Err(_) => {
            let state = app.state::<Arc<Mutex<HashMap<String, PendingCheck>>>>();
            let mut map = state.lock().await;
            map.remove(&request_id);
            Err("Timeout esperando respuesta del sidecar".to_string())
        }
    }
}

#[tauri::command]
pub async fn download_whisper_model(app: tauri::AppHandle) -> Result<(), String> {
    let message = serde_json::json!({
        "id": Uuid::new_v4().to_string(),
        "command": "download_model",
        "payload": {}
    });
    write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error: {}", e))
}

#[tauri::command]
pub fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
