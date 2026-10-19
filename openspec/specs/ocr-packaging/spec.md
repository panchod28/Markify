# ocr-packaging Specification

## Purpose
TBD - created by archiving change add-ocr-image-pdf-support. Update Purpose after archive.

## Requirements

### Requirement: Modelos OCR incluidos en el instalador
El sistema SHALL distribuir los modelos OCR dentro del binario del sidecar y SHALL resolverlos mediante `resource_path()`, de modo que el OCR funcione sin red desde el primer arranque y sin descargas ni diálogos adicionales.

#### Scenario: Primer arranque sin internet
- **WHEN** se instala la app en un equipo sin red y se convierte una imagen
- **THEN** el OCR funciona sin mostrar ningún diálogo de descarga

### Requirement: Integridad de modelos y licencias
El build SHALL obtener los modelos con versión y SHA-256 fijados y fallar si el checksum no coincide. El instalador SHALL incluir los avisos de licencia de los componentes OCR.

#### Scenario: Checksum inválido
- **WHEN** el modelo descargado en CI no coincide con el hash fijado
- **THEN** el build del sidecar falla antes de empaquetar

### Requirement: Dependencias declaradas y reproducibles
`requirements.txt` SHALL listar todas las dependencias del sidecar (incluidas las de OCR y PDF) con versiones acotadas, y el workflow de release SHALL instalar desde ese archivo.

#### Scenario: Entorno limpio
- **WHEN** se crea un entorno nuevo con `pip install -r sidecar/requirements.txt`
- **THEN** `python build.py` y `pytest` funcionan sin pasos manuales adicionales

### Requirement: Presupuesto de tamaño y arranque
El sidecar con OCR SHALL cumplir el presupuesto fijado al cerrar el spike (medido en el spike: ≤ +140 MB en disco sin comprimir; arranque en frío sin OCR sin cambios; carga de modelos + primer OCR ≤ 3 s dentro del proceso; RSS pico ≤ 1.5 GB a 150 DPI).

#### Scenario: Medición en CI
- **WHEN** CI construye el sidecar en macOS y Windows
- **THEN** reporta el tamaño y falla si supera el presupuesto

### Requirement: Verificación del binario empaquetado
CI SHALL ejecutar en macOS y Windows un *smoke test* contra el binario ya compilado que convierta una imagen de prueba y un PDF escaneado de prueba por stdin y verifique `file_result` con `status="completed"` y texto esperado.

#### Scenario: Regresión de empaquetado
- **WHEN** un cambio omite un módulo oculto o un modelo del binario
- **THEN** el smoke test falla y el release no se publica

### Requirement: Compatibilidad de plataformas
La funcionalidad SHALL comportarse igual en macOS arm64 y Windows x64, incluidas rutas con espacios, acentos y caracteres no ASCII.

#### Scenario: Ruta Unicode en Windows
- **WHEN** se convierte `C:\Users\José\Documentos\informe escaneado.pdf`
- **THEN** la conversión se completa con el mismo resultado que en macOS
