use serde::{Deserialize, Serialize};
use tauri_plugin_dialog::DialogExt;
use std::io::Write;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ZipFileEntry {
    pub name: String,
    pub content: String,
}

#[tauri::command]
pub async fn save_markdown(
    app: tauri::AppHandle,
    content: String,
    suggested_name: String,
) -> Result<Option<String>, String> {
    let path = app.dialog()
        .file()
        .set_file_name(&suggested_name)
        .add_filter("Markdown", &["md"])
        .blocking_save_file();

    match path {
        Some(p) => {
            let path_buf = p.into_path()
                .map_err(|e| format!("Error obteniendo ruta: {}", e))?;
            let path_str = path_buf.to_string_lossy().to_string();
            std::fs::write(&path_str, content)
                .map_err(|e| format!("Error guardando archivo: {}", e))?;
            Ok(Some(path_str))
        }
        None => Ok(None),
    }
}

#[tauri::command]
pub async fn save_zip(
    app: tauri::AppHandle,
    files: Vec<ZipFileEntry>,
    suggested_name: String,
) -> Result<Option<String>, String> {
    use zip::write::FileOptions;

    let path = app.dialog()
        .file()
        .set_file_name(&suggested_name)
        .add_filter("ZIP", &["zip"])
        .blocking_save_file();

    match path {
        Some(p) => {
            let path_buf = p.into_path()
                .map_err(|e| format!("Error obteniendo ruta: {}", e))?;
            let path_str = path_buf.to_string_lossy().to_string();
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

#[tauri::command]
pub async fn open_in_folder(file_path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .args(["-R", &file_path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(format!("/select,{}", file_path))
            .spawn()
            .map_err(|e| e.to_string())?;
    }

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
