# image-input-ui Specification

## Purpose
TBD - created by archiving change add-ocr-image-pdf-support. Update Purpose after archive.

## Requirements

### Requirement: Categoría de archivo imagen
El frontend SHALL definir `FileCategory = 'document' | 'audio' | 'image'`, `IMAGE_EXTENSIONS` (`png`, `jpg`, `jpeg`, `webp`, `bmp`, `tif`, `tiff`) incluidas en `SUPPORTED_EXTENSIONS`, y `getFileCategory` SHALL devolver `'image'` para ellas. Todos los tipos SHALL vivir en `src/types/index.ts`.

#### Scenario: Soltar una imagen
- **WHEN** el usuario suelta `captura.PNG`
- **THEN** se acepta, se categoriza como `image` y se envía al sidecar con `category: "image"`

#### Scenario: Extensiones existentes
- **WHEN** el usuario suelta un `.pdf`, `.docx` o `.mp3`
- **THEN** la categoría y el flujo son los mismos que antes

### Requirement: Coherencia visual
Los archivos de imagen SHALL mostrar un icono de `lucide-react` registrado en `FILE_ICON_MAP`/`FileIcon` con la misma convención de color y tamaño que los demás tipos. No se añadirán pantallas, modales ni botones nuevos.

#### Scenario: Lista de archivos
- **WHEN** hay un PDF, un MP3 y un PNG en la lista
- **THEN** los tres se renderizan con el mismo layout, espaciado de 8 px y tema claro/oscuro

### Requirement: Indicador de avisos
Cuando un resultado `completed` incluye `warnings`, la fila SHALL mostrar un icono discreto con un tooltip que liste las páginas/etapas afectadas, usando tokens de diseño existentes. Sin avisos, la fila SHALL ser idéntica a la actual.

#### Scenario: PDF con 2 páginas fallidas
- **WHEN** termina un PDF con warnings en las páginas 7 y 12
- **THEN** la fila muestra estado completado, el icono de avisos y el tooltip "Páginas 7, 12: no se pudieron procesar" (ES/EN)

#### Scenario: El resultado sigue siendo utilizable
- **WHEN** el usuario abre la vista previa o guarda un archivo con avisos
- **THEN** funciona igual que con uno sin avisos

### Requirement: Internacionalización
Todo texto nuevo SHALL existir en `locales/es` y `locales/en`, incluidos los mensajes de error por código.

#### Scenario: Cambio de idioma
- **WHEN** el usuario cambia el idioma a inglés
- **THEN** el tooltip de avisos y los errores nuevos aparecen en inglés
