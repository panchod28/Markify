mod commands;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            commands::conversion::start_conversion,
            commands::conversion::cancel_conversion,
            commands::file_system::save_markdown,
            commands::file_system::save_zip,
            commands::file_system::open_in_folder,
            commands::sidecar::check_whisper_model,
            commands::sidecar::download_whisper_model,
            commands::sidecar::get_app_version,
        ])
        .setup(|app| {
            commands::sidecar::spawn_sidecar(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
