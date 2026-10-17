## ADDED Requirements

### Requirement: Artefacto del sidecar en modo onedir
`build.py` SHALL compilar el sidecar con PyInstaller `--onedir` y dejar el resultado en `src-tauri/binaries/markify-sidecar/` con el ejecutable `markify-sidecar` (`.exe` en Windows) y su carpeta `_internal/`. SHALL eliminar el contenido previo del destino antes de compilar.

#### Scenario: Build limpio
- **WHEN** se ejecuta `npm run build:sidecar` en una máquina con un directorio de salida antiguo
- **THEN** el destino contiene únicamente la salida nueva y el ejecutable arranca

#### Scenario: Plataforma no soportada
- **WHEN** `build.py` se ejecuta en un sistema distinto de macOS o Windows
- **THEN** el comportamiento actual (error o soporte Linux existente) no cambia

### Requirement: Symlinks conservados en macOS
La carpeta del sidecar SHALL incluirse en el `.app` conservando sus symlinks (`bundle.macOS.files`), de modo que el tamaño en disco del `.app` no supere el de la carpeta compilada en más de 5 %.

#### Scenario: Bundle de macOS
- **WHEN** se genera el `.app`
- **THEN** `Contents/Resources/sidecar/_internal` contiene los mismos symlinks que la carpeta de origen y `du` del `.app` ≤ 1.05 × (carpeta + app base)

### Requirement: Paridad funcional con el modo onefile
El sidecar compilado en `--onedir` SHALL responder al mismo protocolo (`check_model`, `convert`, `cancel`, `download_model`) con los mismos mensajes que el compilado en `--onefile`.

#### Scenario: Consulta del modelo
- **WHEN** se envía `{"command":"check_model"}` por stdin al ejecutable compilado
- **THEN** responde una línea JSON `{"type":"model_status",...}` y stdout no contiene otro texto

### Requirement: Presupuesto de arranque
A partir de la segunda ejecución en una misma máquina, el sidecar SHALL responder a `check_model` en 3 segundos o menos.

#### Scenario: Medición en CI
- **WHEN** el smoke test ejecuta el sidecar compilado tras un primer arranque de calentamiento
- **THEN** el mejor de dos arranques posteriores responde en ≤ 3 s y el paso falla en caso contrario

### Requirement: Artefacto de CI que conserva permisos
El workflow SHALL transferir el sidecar entre jobs como `tar` (conserva bit de ejecución y symlinks) y SHALL extraerlo en `src-tauri/binaries/` antes de construir la app.

#### Scenario: Ejecutable tras la descarga
- **WHEN** el job `build-app` en macOS extrae el artefacto
- **THEN** `markify-sidecar` tiene permiso de ejecución sin necesidad de `chmod` manual

### Requirement: Verificación antes de publicar
El job de sidecar SHALL ejecutar un smoke test sobre el binario compilado en macOS y Windows, y un fallo SHALL impedir el empaquetado de la app.

#### Scenario: Módulo faltante en el bundle
- **WHEN** un cambio provoca que `_internal/` omita una dependencia
- **THEN** el smoke test falla y no se genera el instalador

### Requirement: Documentación de build
README y CONTRIBUTING SHALL describir que `build:sidecar` genera una carpeta y cómo reconstruirla, y el spec `10-build` SHALL reflejar el nuevo layout.

#### Scenario: Contribuidor con build antiguo
- **WHEN** un contribuidor sigue CONTRIBUTING tras actualizar
- **THEN** sabe que debe reejecutar `npm run build:sidecar` y que la salida es una carpeta
