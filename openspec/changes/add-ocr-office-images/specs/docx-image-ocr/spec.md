## ADDED Requirements

### Requirement: Texto de las imágenes de un DOCX en su posición
El sistema SHALL extraer con OCR local el texto de las imágenes relevantes de un archivo `.docx` y colocarlo en el `.md` exactamente donde estaba la imagen, entre el texto que la rodea, también dentro de tablas y listas.

#### Scenario: Captura entre dos párrafos
- **WHEN** un DOCX tiene un párrafo, una captura con tres líneas de texto y otro párrafo
- **THEN** el `.md` contiene el primer párrafo, el texto de la captura y el segundo párrafo, en ese orden

#### Scenario: Documento que solo contiene imágenes
- **WHEN** un DOCX está formado por imágenes de páginas escaneadas pegadas una tras otra
- **THEN** el `.md` contiene el texto de cada imagen en orden de documento y la conversión termina sin avisos

#### Scenario: Imagen dentro de una tabla
- **WHEN** una celda de tabla contiene una imagen con texto
- **THEN** el texto reconocido aparece en esa celda de la tabla Markdown

### Requirement: Salida limpia de referencias de imagen
El sistema SHALL NOT dejar en el `.md` de un DOCX con imágenes referencias de imagen vacías ni data-URI (`![..](data:...)`). Cada imagen se sustituye por su texto reconocido, por su texto alternativo real o por nada.

#### Scenario: Imagen sin texto ni descripción
- **WHEN** el DOCX contiene una fotografía sin texto y sin texto alternativo
- **THEN** el `.md` no contiene ninguna línea `![`

### Requirement: Ruta rápida sin regresión
Si un DOCX no contiene imágenes, el sistema SHALL delegar en `convert_document` y devolver exactamente el mismo contenido que antes de este change, sin cargar el motor OCR.

#### Scenario: DOCX con texto, tabla y ecuación
- **WHEN** se convierte un DOCX sin ninguna imagen
- **THEN** la salida es idéntica byte a byte a la de `convert_document` y el motor OCR no se carga

### Requirement: Conservación del resto del contenido
Para un DOCX con imágenes, el sistema SHALL generar el resto del contenido (texto, estilos, tablas, listas, ecuaciones) con la misma cadena de conversión que markitdown, de modo que la única diferencia con la salida de `convert_document` sean las líneas de imagen.

#### Scenario: Comparación con markitdown
- **WHEN** se convierte un DOCX con texto, tabla e imágenes
- **THEN** la salida, descontadas las líneas de imagen, es idéntica a la de `convert_document`

### Requirement: Filtrado de imágenes decorativas y duplicadas
El sistema SHALL leer solo imágenes cuyo tamaño en píxeles alcance los umbrales `OFFICE_MIN_SIDE_PX` y `OFFICE_MIN_PIXELS`, y SHALL leer una sola vez las imágenes con contenido idéntico.

#### Scenario: Icono de 48 × 48 px
- **WHEN** el DOCX contiene un icono de 48 × 48 px y una captura de 900 × 420 px
- **THEN** solo la captura se envía al motor OCR

#### Scenario: Logotipo repetido
- **WHEN** la misma imagen aparece en diez posiciones del documento
- **THEN** se ejecuta una sola vez el OCR y el resultado se reutiliza en las posiciones que corresponda

### Requirement: Texto alternativo real
El sistema SHALL conservar el texto alternativo de una imagen cuando sea una descripción real y emitirlo como una línea en cursiva antes del texto reconocido; SHALL descartarlo cuando coincida con un nombre de archivo o con un nombre automático.

#### Scenario: Descripción escrita por el autor
- **WHEN** una imagen tiene el texto alternativo "Captura del sistema"
- **THEN** el `.md` contiene `*Captura del sistema*` seguido del texto reconocido de la imagen

#### Scenario: Nombre automático
- **WHEN** el texto alternativo es "image.png" o "Imagen 3"
- **THEN** no aparece en el `.md`

### Requirement: Imágenes de página y orientación
Si una imagen ocupa lo que una página (ambos lados ≥ `OFFICE_PAGE_LIKE_PX`), el sistema SHALL usar la lectura con reintento de orientación del pipeline de PDF; para el resto de imágenes SHALL ejecutar un único OCR a 0°.

#### Scenario: Escaneo girado 180° pegado en el documento
- **WHEN** el DOCX contiene una imagen de página completa girada 180°
- **THEN** el `.md` contiene su texto legible

#### Scenario: Figura pequeña sin texto
- **WHEN** una figura relevante no contiene texto
- **THEN** se ejecuta una sola inferencia y no se emite aviso

### Requirement: Aislamiento de fallos por imagen
Una imagen que no se pueda decodificar o reconocer SHALL NOT abortar el archivo: se registra un aviso `image_failed` y el resto del documento se convierte.

#### Scenario: Imagen corrupta
- **WHEN** una de tres imágenes del DOCX tiene bytes corruptos
- **THEN** el `.md` contiene el texto del documento y de las otras dos imágenes, y el resultado incluye un aviso `image_failed`
