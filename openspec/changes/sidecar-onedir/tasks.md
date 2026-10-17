> Cambio de empaquetado: no toca la lógica de conversión. Prerrequisito de `add-ocr-image-pdf-support`.

## 1. Spike de integración (descartable)

- [x] 1.1 En macOS: sidecar `--onedir` real + app Tauri con `shell().command(ruta)`: ejecución, bit de ejecución y ruta en `Contents/Resources/sidecar/` confirmados. Hallazgo: `bundle.resources` desreferencia symlinks (+277 MB); se usa `bundle.macOS.files`
- [x] 1.2 `app.shell().command()` desde Rust funciona sin scope de capabilities (verificado en release y dev)
- [x] 1.3 `tauri dev`: se usa `CARGO_MANIFEST_DIR/binaries/markify-sidecar` bajo `cfg!(debug_assertions)`; sin copia a `target/`; sidecar arranca como hijo de la app
- [ ] 1.4 Repetir en Windows (runner CI o VM): instalador MSI/NSIS, tiempo de instalación, primer y segundo arranque, rutas máximas
- [x] 1.5 Decisión tomada y reflejada en `design.md` (D2); falta confirmar la fila de Windows con 1.4

## 2. Build del sidecar

- [x] 2.1 `sidecar/build.py`: `--onedir`, destino `src-tauri/binaries/markify-sidecar/`, limpieza previa, mantener flags y hooks existentes
- [x] 2.2 Hacer que `build.py` funcione desde un entorno limpio: flags para numpy ≥ 2.4 (`numpy._core`, `numpy.lib`), ruta `setuptools/_vendor`, y `requirements.txt` con los extras faltantes (`markitdown[all]`/pdf, `python-pptx`, `openpyxl`, `xlrd`)
- [x] 2.3 Verificado en macOS (entorno limpio desde `requirements.txt`): `check_model` y `convert` (CSV, HTML, archivo inexistente) correctos; primer arranque 47.5 s (una vez), siguientes 2.0 s

## 3. Integración con Tauri

- [x] 3.1 `tauri.conf.json`: quitar `externalBin`; crear `tauri.macos.conf.json` (`bundle.macOS.files`) y `tauri.windows.conf.json` (`bundle.resources`) según D2
- [x] 3.2 `commands/sidecar.rs`: ruta por `cfg!(debug_assertions)` (dev) o `BaseDirectory::Resource` (instalado), lanzar con `shell().command()`, error con ruta buscada; `SidecarState` y el resto sin cambios (prototipo funcional en el spike)
- [x] 3.3 `check_whisper_model`: timeout con constante nombrada (60 s)
- [x] 3.4 `useConversionStore.checkWhisperModel`: capturar error sin modificar el estado ni abrir el modal
- [x] 3.5 Quitar `shell:allow-spawn` de `capabilities/default.json` si ya no se usa desde JS y comprobar que la app sigue funcionando
- [x] 3.6 Verificado en macOS: `tauri dev` y `.app` de release lanzan el sidecar como hijo de la app y no dejan procesos al cerrar; conversión probada contra el sidecar del bundle por stdin. **No probado**: conversión desde la UI, transcripción de audio y cancelación

## 4. CI

- [x] 4.1 `release.yml`: empaquetar el sidecar como `tar`, subirlo y extraerlo en `build-app`; eliminar el `chmod` suelto
- [x] 4.2 `sidecar/smoke_test.py` + paso en CI (macOS y Windows): protocolo JSON puro, conversión de CSV y mejor de dos arranques posteriores ≤ 3 s. Probado en local (pasa, falla con presupuesto menor o carpeta ausente); **no ejecutado aún en runners**
- [x] 4.3 Actualizar patrones de artefacto y la ruta de salida del job de sidecar

## 5. Verificación de instaladores

- [x] 5.1 Instalar el `.dmg` en macOS: primera apertura, segunda apertura, conversión de documento y audio. *Hecho en macOS con la copia del `.dmg` montado (app abierta, sidecar en `Resources/sidecar`): desde la UI se convirtieron DOCX, PDF, HTML y CSV ("4 archivos convertidos correctamente", vista previa con acentos correcta); se descargó el modelo Whisper desde el modal (145 MB) y se transcribió un audio de 6 s; se pulsó Cancelar durante la transcripción de un audio de 113 s. **Pendiente**: instalación en una máquina limpia (otro equipo)*
- [ ] 5.2 Instalar el `.msi`/`.exe` en VM Windows limpia: igual que 5.1; medir tiempo de instalación y escaneo del antivirus
- [x] 5.3 Sin `_MEI*` ni procesos tras cerrar la app (normal y `kill -9`) en macOS
- [x] 5.4 Tamaño comparado like-for-like: DMG `--onefile` 305 MB vs `--onedir` 357 MB (+17 %); ver D6. Nota: `bundle_dmg.sh` de Tauri falla en esta sesión (requiere sesión gráfica de Finder), el DMG se generó con `hdiutil` UDZO

## 6. Documentación y cierre

- [x] 6.1 README y CONTRIBUTING: build del sidecar como carpeta, requisitos del entorno
- [x] 6.2 Actualizar specs planos `04-tauri-commands` y `10-build`
- [ ] 6.3 Anotar como issues separados (ninguno es causado por este change; verificados en el build `--onedir` y presentes en `main`):
  - `check_model` responde `model_status` **sin `request_id`** y Rust busca ese campo, así que `check_whisper_model` siempre expira: la UI muestra el modal de descarga de Whisper aunque el modelo exista (se vuelve a descargar) y `resetToEmpty` además reinicia `whisperModelAvailable`
  - **Cancelar no interrumpe una conversión en curso**: el bucle de `main.py` lee `cancel` del stdin solo cuando `handle_convert` termina; al cancelar un audio de 113 s la UI quedó en "Cancelando…" ~2 min y terminó como "convertido correctamente"
  - el modelo Whisper se guarda junto al ejecutable (dentro del `.app`; se pierde al actualizar y no es escribible en `Program Files`)
  - firmado/notarización de `Resources/sidecar`
- [ ] 6.4 `openspec validate sidecar-onedir --strict` y archivar
