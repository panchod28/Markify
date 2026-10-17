## ADDED Requirements

### Requirement: Texto de las imágenes de un PPTX en la posición de la imagen
El sistema SHALL extraer con OCR local el texto de las imágenes relevantes de un archivo `.pptx`, incluidas las de marcadores de posición y las de grupos de formas, y SHALL colocarlo en el `.md` en la posición que la imagen ocupa en su diapositiva.

#### Scenario: Diapositiva con título, texto e imagen
- **WHEN** una diapositiva tiene un título, una captura con texto debajo y un cuadro de texto
- **THEN** el `.md` contiene el título, el texto de la captura y el cuadro de texto en el orden de lectura de la diapositiva

#### Scenario: Imagen dentro de un grupo
- **WHEN** la única imagen con texto de una diapositiva está dentro de un grupo de formas
- **THEN** su texto reconocido aparece en el `.md` de esa diapositiva

#### Scenario: Diapositiva que es solo una imagen
- **WHEN** una diapositiva contiene únicamente una imagen de página completa con texto
- **THEN** el `.md` de esa diapositiva contiene el texto de la imagen bajo su marcador de diapositiva

### Requirement: Salida limpia de referencias de imagen
El sistema SHALL NOT dejar en el `.md` de un PPTX con imágenes enlaces de imagen inexistentes (`![..](Nombre.jpg)`). Cada imagen se sustituye por su texto reconocido, por su texto alternativo real o por nada.

#### Scenario: Diapositiva con iconos decorativos
- **WHEN** una diapositiva tiene tres iconos sin texto alternativo
- **THEN** el `.md` de esa diapositiva no contiene ninguna línea `![`

### Requirement: Ruta rápida sin regresión
Si un PPTX no contiene imágenes, el sistema SHALL delegar en `convert_document` y devolver exactamente el mismo contenido que antes de este change, sin cargar el motor OCR.

#### Scenario: PPTX solo de texto
- **WHEN** se convierte un PPTX sin ninguna imagen
- **THEN** la salida es idéntica byte a byte a la de `convert_document` y el motor OCR no se carga

### Requirement: Conservación del resto del contenido
Para un PPTX con imágenes, el sistema SHALL generar el resto del contenido (títulos, texto, tablas, gráficos, marcadores `<!-- Slide number: N -->` y notas) con markitdown sin alterarlo, de modo que la única diferencia con `convert_document` sean las líneas de imagen.

#### Scenario: Comparación con markitdown
- **WHEN** se convierte un PPTX con tabla, notas e imágenes
- **THEN** la salida, descontadas las líneas de imagen y el texto añadido por ellas, es idéntica a la de `convert_document`

### Requirement: Filtrado de imágenes decorativas y duplicadas
El sistema SHALL leer solo imágenes cuya forma ocupe al menos `OFFICE_MIN_AREA` (1 %) de la diapositiva, SHALL leer una sola vez las imágenes con contenido idéntico y emitir su texto solo en la primera aparición.

#### Scenario: Deck con logos e iconos
- **WHEN** un PPTX tiene 28 imágenes y solo 9 ocupan al menos el 1 % de su diapositiva
- **THEN** solo esas 9 se envían al motor OCR

#### Scenario: Logotipo repetido en varias diapositivas
- **WHEN** el mismo logotipo, con texto, aparece en tres diapositivas
- **THEN** se ejecuta una sola vez el OCR y su texto aparece solo en la primera diapositiva

### Requirement: Descarte de texto sin valor
El sistema SHALL descartar el texto reconocido de una imagen cuando tenga menos de `OFFICE_MIN_TEXT_CHARS` caracteres alfanuméricos, sin emitir aviso.

#### Scenario: Icono de 512 px que "lee" un carácter
- **WHEN** el OCR devuelve un solo carácter para un icono de una diapositiva
- **THEN** el `.md` no contiene ese carácter ni líneas de imagen

### Requirement: Texto alternativo real
El sistema SHALL conservar el texto alternativo (`descr`) de una imagen cuando sea una descripción real **y la imagen sea relevante (≥ `OFFICE_MIN_AREA` de la diapositiva) o aporte texto**, y emitirlo como línea en cursiva antes del texto reconocido; SHALL descartarlo cuando coincida con el nombre de la forma, con un nombre de archivo o con un nombre automático, y SHALL ignorar el de imágenes pequeñas que no aportan texto (iconos), cuya descripción suele ser un título copiado de la web.

#### Scenario: Imagen relevante con descripción del autor
- **WHEN** una captura de 12 % de la diapositiva y sin texto reconocible tiene el texto alternativo "Captura del sistema"
- **THEN** el `.md` contiene `*Captura del sistema*`

#### Scenario: Icono con descripción
- **WHEN** un icono de 0.2 % de la diapositiva tiene el texto alternativo "Correo de contacto"
- **THEN** el `.md` no contiene esa descripción y no se ejecuta OCR sobre el icono

#### Scenario: Nombre de archivo como descripción
- **WHEN** el texto alternativo es `image.png`
- **THEN** no aparece en el `.md`

### Requirement: Imágenes de diapositiva completa y orientación
Si una imagen cubre al menos `SCAN_COVERAGE` de la diapositiva, el sistema SHALL usar la lectura con reintento de orientación; para el resto SHALL ejecutar un único OCR a 0°.

#### Scenario: Diapositiva escaneada girada
- **WHEN** una diapositiva es una imagen de página completa girada 180°
- **THEN** el `.md` contiene su texto legible

### Requirement: Aislamiento de fallos por imagen
Una imagen que no se pueda decodificar o reconocer SHALL NOT abortar el archivo: se registra un aviso `image_failed` con el número de diapositiva y el resto de la presentación se convierte.

#### Scenario: Imagen corrupta en la diapositiva 4
- **WHEN** la imagen de la diapositiva 4 tiene bytes corruptos
- **THEN** el `.md` contiene el resto de la presentación y el resultado incluye un aviso `image_failed` con `page=4`
