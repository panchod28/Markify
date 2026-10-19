## ADDED Requirements

### Requirement: Clasificación por página
El sistema SHALL clasificar cada página de un PDF como `TEXT`, `SCANNED`, `MIXED` o `BLANK` a partir de métricas medidas (caracteres de texto y área cubierta por imágenes) usando una función pura con umbrales centralizados.

#### Scenario: Página con texto
- **WHEN** una página tiene 800 caracteres de texto y ninguna imagen relevante
- **THEN** se clasifica `TEXT`

#### Scenario: Página escaneada
- **WHEN** una página tiene 0 caracteres de texto y una imagen que cubre el 95 % del área
- **THEN** se clasifica `SCANNED`

#### Scenario: Escaneo con capa de texto previa
- **WHEN** una página tiene una imagen de página completa y una capa de texto con más de `MIN_TEXT_CHARS` caracteres
- **THEN** se clasifica `TEXT` y no se ejecuta OCR

#### Scenario: Página mixta
- **WHEN** una página tiene texto nativo y una imagen de al menos `IMAGE_MIN_AREA` que no es fondo completo
- **THEN** se clasifica `MIXED`

#### Scenario: Decoración
- **WHEN** una página con texto contiene solo un logotipo menor que `IMAGE_MIN_AREA`
- **THEN** se clasifica `TEXT` sin OCR

#### Scenario: Página en blanco
- **WHEN** una página no tiene texto ni imágenes
- **THEN** se clasifica `BLANK`, se omite sin warning y no cuenta como fallo

### Requirement: Ruta rápida sin regresión para PDFs de texto
Si todas las páginas son `TEXT` o `BLANK`, el sistema SHALL delegar en `convert_document` y devolver exactamente el mismo contenido que antes de este change.

#### Scenario: PDF de texto con tablas
- **WHEN** se convierte un PDF de solo texto con tablas
- **THEN** la salida es idéntica byte a byte a la de `convert_document` y no se carga el motor OCR

### Requirement: Ruta híbrida por página
Si al menos una página es `SCANNED` o `MIXED`, el sistema SHALL procesar cada página según su clase y unir los resultados en orden de página separados por una línea en blanco.

#### Scenario: Documento mezclado
- **WHEN** un PDF de 10 páginas tiene 6 de texto, 3 escaneadas y 1 en blanco
- **THEN** el `.md` contiene el texto nativo de las 6, el OCR de las 3 y nada para la blanca, en orden

#### Scenario: Página mixta
- **WHEN** una página `MIXED` contiene un párrafo y una imagen con un diagrama rotulado
- **THEN** la salida contiene el párrafo seguido del texto OCR de la imagen, sin duplicar texto

### Requirement: Aislamiento de fallos por página
Un fallo de render u OCR en una página SHALL NOT abortar el archivo. La página se sustituye por un comentario `<!-- Markify: página N no se pudo procesar (code) -->` y se registra un `PageIssue`.

#### Scenario: Página corrupta
- **WHEN** la página 7 de 20 lanza una excepción al renderizar
- **THEN** el `.md` contiene las otras 19 páginas, el marcador de la 7 con el código de causa `(page_render_failed)` y un warning `{page: 7, stage: "render", code: "page_failed"}`

#### Scenario: Todas las páginas fallan
- **WHEN** ninguna página produce texto y al menos una falló
- **THEN** el archivo se marca con error con el `code` del primer fallo, no con "sin texto"

### Requirement: Errores fatales del archivo
El sistema SHALL tratar como error del archivo únicamente: contraseña de apertura requerida (`pdf_encrypted`, mismo mensaje que hoy), archivo no abrible (`pdf_open_failed`), cero páginas, o ausencia total de contenido sin fallos de página (`no_text_found`).

#### Scenario: PDF cifrado
- **WHEN** se convierte un PDF que requiere contraseña para abrirse
- **THEN** se lanza `PermissionError` y la UI muestra el mensaje actual "protegido con contraseña"

### Requirement: Cancelación y progreso por página
El sistema SHALL consultar el `cancel_flag` antes de cada página y emitir `file_progress` con el porcentaje de páginas procesadas en la ruta híbrida.

#### Scenario: Cancelar a mitad de un PDF escaneado
- **WHEN** el usuario cancela mientras se procesa la página 12 de 100
- **THEN** el pipeline termina antes de iniciar la página 13 y se emite `conversion_cancelled`

#### Scenario: Progreso
- **WHEN** se han procesado 25 de 100 páginas
- **THEN** el último `file_progress` tiene `progress=25`

### Requirement: Orientación a nivel de página
Si el OCR a 0° no detecta texto en una página `SCANNED`, el sistema SHALL reintentar a 90°, 180° y 270° y conservar la orientación con mayor suma de `confianza × longitud`. Si ninguna produce texto, la página se trata como fallo de OCR con warning.

#### Scenario: Escaneo girado 180°
- **WHEN** una página escaneada está girada 180°
- **THEN** el `.md` contiene su texto legible y no se registra warning

#### Scenario: Página recta
- **WHEN** el OCR a 0° encuentra texto
- **THEN** no se ejecutan reintentos de rotación

### Requirement: Uso acotado de memoria
El sistema SHALL mantener como máximo una página rasterizada en memoria y liberarla antes de pasar a la siguiente.

#### Scenario: PDF escaneado de 200 páginas
- **WHEN** se procesa el documento completo a 150 DPI
- **THEN** la memoria pico no crece con el número de páginas y se mantiene ≤ 1.5 GB
