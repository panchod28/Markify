# ocr-shared-recognition Specification

## Purpose
TBD - created by archiving change add-ocr-office-images. Update Purpose after archive.

## Requirements

### Requirement: Carga de imágenes desde bytes
El sistema SHALL ofrecer una carga común de imágenes (ruta o bytes) que aplique orientación EXIF, componga la transparencia sobre fondo blanco, convierta a RGB, rechace imágenes que excedan el límite de píxeles con `image_too_large` y los archivos no decodificables con `image_decode_failed`, y reduzca el lado mayor al máximo configurado (2 000 px por defecto) sin ampliar nunca imágenes pequeñas.

#### Scenario: PNG con transparencia
- **WHEN** se carga un PNG de texto negro sobre fondo transparente
- **THEN** el resultado es una imagen RGB con el texto negro sobre fondo blanco

#### Scenario: Bytes que no son una imagen
- **WHEN** se cargan bytes arbitrarios
- **THEN** se lanza `ConversionError(code="image_decode_failed")`

### Requirement: Lectura con reintento de orientación reutilizable
El sistema SHALL ofrecer una lectura de imagen con el reintento de orientación 90/180/270° y la regla de "solo líneas horizontales" del pipeline de PDF, y una lectura simple de un único OCR a 0°, ambas devolviendo el texto y el número de líneas descartadas por baja confianza.

#### Scenario: Página recta
- **WHEN** el OCR a 0° encuentra texto horizontal
- **THEN** no se ejecutan reintentos de rotación

#### Scenario: Lectura simple
- **WHEN** se solicita la lectura simple de una imagen sin texto
- **THEN** se ejecuta una sola inferencia y se devuelve texto vacío sin lanzar error

### Requirement: Sin regresión en imágenes sueltas y PDFs
La extracción de los módulos compartidos SHALL NOT cambiar la salida, los avisos ni los errores de la conversión de imágenes sueltas ni de PDFs. La única diferencia admitida es que las imágenes con transparencia se componen sobre fondo blanco en lugar de descartar el canal alfa (el texto negro sobre fondo transparente era ilegible).

#### Scenario: Suite existente
- **WHEN** se ejecutan los tests de imágenes, de PDF y de layout existentes tras el refactor
- **THEN** todos pasan sin modificar sus expectativas
