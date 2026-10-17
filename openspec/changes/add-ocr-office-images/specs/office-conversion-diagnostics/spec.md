## ADDED Requirements

### Requirement: Aviso de imagen fallida
El sistema SHALL registrar un aviso `image_failed` por cada imagen que no se pueda decodificar o reconocer, con la etapa (`decode` u `ocr`) y, en PPTX, el número de diapositiva; en DOCX `page` es `null`. Cada incidente SHALL escribirse en stderr en una línea con archivo, etapa y código, sin contenido del documento ni rutas completas.

#### Scenario: Fallo en una diapositiva
- **WHEN** falla la lectura de una imagen de la diapositiva 7
- **THEN** `file_result.payload.warnings` contiene `{page: 7, stage: "ocr", code: "image_failed"}` con el mensaje localizado que nombra la diapositiva

#### Scenario: Fallo en un DOCX
- **WHEN** falla la lectura de una imagen de un DOCX
- **THEN** el aviso tiene `page: null` y un mensaje que no menciona diapositivas

### Requirement: Aviso agregado de imágenes omitidas
El sistema SHALL contar en un único aviso `images_skipped` (con `count`) las imágenes de un formato que Pillow no puede abrir (por ejemplo EMF o WMF), sin que ese aviso aborte la conversión.

#### Scenario: Documento con dos imágenes EMF
- **WHEN** un DOCX contiene dos imágenes EMF y una captura PNG
- **THEN** se lee la captura y el resultado incluye un único aviso `images_skipped` con `count=2`

### Requirement: Mensajes ES/EN
Todo código nuevo (`image_failed`, `images_skipped`, `legacy_format`) SHALL tener mensaje en español e inglés en `error_messages.py` y, los que se muestren en la interfaz, en `i18n`.

#### Scenario: Código sin traducción
- **WHEN** se ejecuta el test de cobertura de códigos
- **THEN** falla si algún código usado en `ocr/` carece de mensaje o plantilla en alguno de los dos idiomas

### Requirement: Progreso y cancelación por imagen
Durante la conversión de un DOCX o PPTX con imágenes por leer, el sistema SHALL emitir `file_progress` con el porcentaje de imágenes procesadas (0–99, sin `warnings` ni `markdownContent`) y SHALL consultar `cancel_flag` antes de cada imagen; al cancelar devuelve `""` y el sidecar emite `conversion_cancelled`.

#### Scenario: Cancelar a mitad
- **WHEN** el usuario cancela mientras se lee la imagen 3 de 10
- **THEN** no se inicia la imagen 4 y se emite `conversion_cancelled`

#### Scenario: Progreso
- **WHEN** se han leído 5 de 10 imágenes
- **THEN** el último `file_progress` tiene `progress=50`
