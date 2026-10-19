# ocr-engine Specification

## Purpose
TBD - created by archiving change add-ocr-image-pdf-support. Update Purpose after archive.

## Requirements

### Requirement: Interfaz de motor OCR reemplazable
El sistema SHALL exponer un `OcrEngine` con un único método `recognize(image) -> list[OcrLine]`, donde `OcrLine` contiene `text`, `box` y `confidence`. Los consumidores SHALL depender solo de esta interfaz y nunca importar el motor concreto.

#### Scenario: Motor sustituido en pruebas
- **WHEN** el pipeline recibe un `OcrEngine` de prueba que devuelve líneas fijas
- **THEN** produce el Markdown esperado sin cargar RapidOCR ni modelos

#### Scenario: Motor nuevo en el futuro
- **WHEN** se añade una implementación de `OcrEngine` y una entrada en el registro `ENGINES`
- **THEN** no se modifica `image_converter`, `pdf_pipeline` ni `layout`

### Requirement: Motor por defecto RapidOCR sobre ONNX Runtime
El sistema SHALL usar RapidOCR con ONNX Runtime en CPU, sin GPU ni acceso a red, con los modelos PP-OCRv5 de detección (mobile) y reconocimiento `latin` (cubre español e inglés), cargados siempre desde rutas explícitas locales. El clasificador de orientación de línea SHALL permanecer desactivado.

#### Scenario: Reconocimiento de español
- **WHEN** se procesa una imagen con el texto "Canción de la niña: ¿cómo estás?"
- **THEN** el resultado conserva tildes, "ñ" y los signos "¿" y "?" con CER dentro del objetivo del corpus

#### Scenario: Sin conexión
- **WHEN** el equipo no tiene red (o las conexiones salientes están bloqueadas) y se procesa una imagen
- **THEN** el OCR funciona sin intentar ninguna conexión ni descargar modelos

#### Scenario: Página recta sin desorden de líneas
- **WHEN** se procesa una página recta de texto corrido
- **THEN** no hay líneas ilegibles introducidas por un clasificador de orientación de línea

### Requirement: Inicialización perezosa y única
El sistema SHALL cargar el motor y sus modelos la primera vez que se necesite OCR y reutilizar esa instancia después. Convertir documentos o audio SHALL NOT importar ni cargar el motor OCR.

#### Scenario: Conversión sin OCR
- **WHEN** se convierte un DOCX o un PDF de solo texto
- **THEN** los módulos de OCR no se importan y el tiempo de arranque no aumenta

#### Scenario: Varias imágenes seguidas
- **WHEN** se convierten 3 imágenes en el mismo lote
- **THEN** los modelos se cargan una sola vez

### Requirement: Fallo de carga del motor reportado con contexto
Si el motor no puede inicializarse (modelo ausente, runtime incompatible), el sistema SHALL lanzar `ConversionError(code="ocr_engine_unavailable", stage="ocr")` indicando qué recurso falló, sin afectar a las demás conversiones del lote.

#### Scenario: Modelo ausente
- **WHEN** falta el archivo del modelo de reconocimiento
- **THEN** el archivo falla con `ocr_engine_unavailable`, se registra la ruta lógica del recurso en stderr y el siguiente archivo del lote se procesa normalmente
