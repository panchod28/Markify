use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FilePayload {
    pub id: String,
    pub path: String,
    pub category: String,
}

#[tauri::command]
pub async fn start_conversion(
    app: tauri::AppHandle,
    files: Vec<FilePayload>,
    lang: String,
) -> Result<(), String> {
    let message = serde_json::json!({
        "id": uuid::Uuid::new_v4().to_string(),
        "command": "convert",
        "payload": {
            "files": files,
            "lang": lang
        }
    });
    crate::commands::sidecar::write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error enviando al sidecar: {}", e))
}

#[tauri::command]
pub async fn cancel_conversion(app: tauri::AppHandle) -> Result<(), String> {
    let message = serde_json::json!({
        "id": uuid::Uuid::new_v4().to_string(),
        "command": "cancel",
        "payload": {}
    });
    crate::commands::sidecar::write_to_sidecar(&app, &message.to_string()).await
        .map_err(|e| format!("Error cancelando: {}", e))
}
