# image-conversion Specification

## Purpose
TBD - created by archiving change add-ocr-image-pdf-support. Update Purpose after archive.

## Requirements

### Requirement: Conversión de imágenes a Markdown
El sistema SHALL convertir archivos `png`, `jpg`, `jpeg`, `webp`, `bmp`, `tif` y `tiff` a Markdown extrayendo su texto con OCR local. La salida SHALL contener solo el texto reconocido, sin encabezado añadido.

#### Scenario: Imagen con texto
- **WHEN** se convierte una captura de pantalla con tres párrafos
- **THEN** el `.md` contiene los tres párrafos separados por línea en blanco y en orden de lectura

#### Scenario: Imagen sin texto
- **WHEN** se convierte una fotografía sin texto reconocible
- **THEN** el archivo termina con el error existente "No se encontró texto en el archivo" (`code=no_text_found`)

### Requirement: Orientación y normalización de entrada
El sistema SHALL aplicar la orientación EXIF, convertir a RGB y, si la imagen supera el máximo de píxeles configurado, reducirla antes del OCR.

#### Scenario: Foto de móvil rotada por EXIF
- **WHEN** la imagen tiene orientación EXIF 6
- **THEN** el OCR se ejecuta sobre la imagen ya enderezada

### Requirement: Límites de seguridad
El sistema SHALL rechazar imágenes que excedan el límite de descompresión de Pillow con `ConversionError(code="image_too_large")`, y archivos no decodificables con `code="image_decode_failed"`, sin agotar la memoria.

#### Scenario: Bomba de descompresión
- **WHEN** se convierte una imagen cuyas dimensiones declaradas exceden el límite
- **THEN** falla con `image_too_large` y el sidecar sigue operativo

#### Scenario: Archivo con extensión de imagen pero corrupto
- **WHEN** un `.png` contiene bytes arbitrarios
- **THEN** falla con `image_decode_failed` y el mensaje de usuario existente de "archivo dañado"

### Requirement: Filtrado por confianza
El sistema SHALL descartar líneas con confianza inferior a `MIN_CONFIDENCE` y reportar la cantidad descartada como un único warning agregado.

#### Scenario: Ruido en una foto
- **WHEN** el motor devuelve 40 líneas y 6 están por debajo del umbral
- **THEN** el `.md` contiene 34 líneas y un warning `low_confidence_dropped` con `count=6`

### Requirement: TIFF multipágina
El sistema SHALL procesar solo el primer fotograma de un TIFF multipágina y emitir un warning indicando que se omitieron los demás.

#### Scenario: TIFF de 3 fotogramas
- **WHEN** se convierte un TIFF con 3 fotogramas
- **THEN** el `.md` contiene el texto del primero y un warning `frames_skipped`
