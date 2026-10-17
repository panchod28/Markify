## ADDED Requirements

### Requirement: Localización del sidecar empaquetado
La app SHALL lanzar el sidecar desde Rust sin depender de `externalBin`: instalada, desde `<recursos>/sidecar/markify-sidecar[.exe]`; en `tauri dev`, directamente desde `src-tauri/binaries/markify-sidecar/` sin copiarlo.

#### Scenario: Instalador macOS
- **WHEN** se abre la app instalada desde el `.dmg`
- **THEN** el sidecar arranca desde `Contents/Resources/sidecar/` y la app puede convertir un archivo

#### Scenario: Instalador Windows
- **WHEN** se abre la app instalada con el `.msi`/`.exe`
- **THEN** el sidecar arranca desde la carpeta de recursos de la instalación y la app puede convertir un archivo

#### Scenario: Desarrollo
- **WHEN** se ejecuta `npm run tauri dev` tras `npm run build:sidecar`
- **THEN** el sidecar arranca desde `src-tauri/binaries/markify-sidecar/` sin copiarlo a `target/` ni pasos manuales

### Requirement: Protocolo y estado sin cambios
`SidecarState`, `write_to_sidecar`, el manejo de salida (`handle_sidecar_output`) y los eventos `conversion:*`/`model:*` SHALL conservar su comportamiento y contratos.

#### Scenario: Conversión de un documento
- **WHEN** el usuario convierte un DOCX después del cambio
- **THEN** recibe progreso, resultado y completado con los mismos eventos y payloads que antes

#### Scenario: Cancelación
- **WHEN** el usuario cancela una transcripción en curso
- **THEN** se emite `conversion:cancelled` como antes

### Requirement: Error claro cuando falta el sidecar
Si el ejecutable no existe o no puede lanzarse, `spawn_sidecar` SHALL devolver un error que incluya la ruta buscada y el motivo, visible en stderr de la app.

#### Scenario: Carpeta ausente
- **WHEN** se ejecuta la app sin haber compilado el sidecar
- **THEN** el log indica `Sidecar no encontrado en <ruta>` con instrucciones de ejecutar `npm run build:sidecar`

### Requirement: Tolerancia al primer arranque lento
`check_whisper_model` SHALL esperar hasta 60 s la respuesta del sidecar y el frontend SHALL capturar su fallo sin alterar `whisperModelAvailable` ni abrir el modal de descarga por error.

#### Scenario: Primer arranque en macOS
- **WHEN** el sidecar tarda 26 s en responder tras instalar la app
- **THEN** `checkWhisperModel` resuelve con el valor real y la UI no muestra errores

#### Scenario: Sidecar caído
- **WHEN** el sidecar no responde en 60 s
- **THEN** se registra el error, el estado previo se conserva y la app sigue usable para documentos

### Requirement: Sin procesos ni temporales huérfanos
Cerrar la app SHALL terminar el proceso del sidecar sin dejar directorios temporales de extracción.

#### Scenario: Cierre forzado
- **WHEN** se fuerza el cierre de la app
- **THEN** no queda un directorio `_MEI*` de ~570 MB en el temporal del sistema
