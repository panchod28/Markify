# conversion-diagnostics Specification

## Purpose
TBD - created by archiving change add-ocr-image-pdf-support. Update Purpose after archive.

## Requirements

### Requirement: Error de conversión estructurado
El sistema SHALL definir `ConversionError` con `code` estable, `stage`, `file`, `page` opcional y causa original. Los códigos SHALL ser un conjunto cerrado y documentado.

#### Scenario: Error con contexto completo
- **WHEN** falla el OCR de la página 4 de `informe.pdf`
- **THEN** la excepción expone `code="ocr_failed"`, `stage="ocr"`, `file="informe.pdf"`, `page=4` y la causa original encadenada

### Requirement: Log trazable sin datos sensibles
Cada incidente SHALL registrarse en stderr en una línea con `file`, `page`, `stage`, `code` y tipo/mensaje del error, más traceback. El log SHALL NOT incluir el contenido del documento ni la ruta completa del archivo, y SHALL NOT escribir nada en stdout.

#### Scenario: Incidente de página
- **WHEN** falla una página
- **THEN** stderr contiene `[Sidecar][ocr] file=informe.pdf page=4 stage=ocr code=ocr_failed ...` y stdout solo contiene mensajes JSON del protocolo

### Requirement: Mensajes de usuario por código
`get_error_message` SHALL resolver primero el `code` de la excepción en el diccionario ES/EN y, si no existe, aplicar el comportamiento actual por nombre de excepción. Todos los códigos nuevos SHALL tener mensaje en ES y EN.

#### Scenario: Código conocido
- **WHEN** se lanza `ConversionError(code="image_too_large")` con `lang="es"`
- **THEN** el mensaje es el texto en español definido para ese código

#### Scenario: Compatibilidad
- **WHEN** se lanza `PermissionError` o `ValueError` sin `code`
- **THEN** el mensaje es el mismo que antes del change

### Requirement: Warnings en el protocolo
El mensaje `file_result` SHALL poder incluir `warnings: [{page, stage, code, message}]`. Si no hay avisos el campo SHALL omitirse. Los mensajes de progreso SHALL NOT incluir `warnings`.

#### Scenario: Conversión con avisos
- **WHEN** un PDF termina con 2 páginas fallidas
- **THEN** `file_result` tiene `status="completed"`, `markdownContent` y `warnings` con 2 elementos

#### Scenario: Conversión sin avisos
- **WHEN** un DOCX se convierte correctamente
- **THEN** `file_result` es idéntico al actual (sin campo `warnings`)
