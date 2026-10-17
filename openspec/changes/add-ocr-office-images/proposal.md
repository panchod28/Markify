## Why

El change `add-ocr-image-pdf-support` leyó imágenes y PDFs escaneados, pero DOCX y PPTX —junto con PDF, los formatos más usados— siguen perdiendo todo lo que está dentro de una imagen. Verificado en markitdown 0.1.6:

- **PPTX**: cada imagen sale como `![alt](Nombre.jpg)`, un enlace a un archivo que no existe (en la UI se ven como cuadros "?"); el texto de la imagen no se extrae.
- **DOCX**: cada imagen sale como `![](data:image/png;base64...)` recortado; tampoco se extrae su texto.

Es el mismo hueco que tenían los PDFs escaneados: capturas, diagramas rotulados, tablas pegadas como imagen y documentos escaneados insertados en Word/PowerPoint quedan fuera del Markdown que se le da a un LLM, y además se ensucia la salida con referencias inútiles. Aparte, la app acepta `.doc` y `.ppt` (binarios OLE antiguos) en el selector aunque markitdown no los soporta: el usuario recibe "Error inesperado al convertir el archivo".

## What Changes

- **OCR de imágenes dentro de DOCX y PPTX**, 100 % local y con el motor del change anterior (`OcrEngine`, `layout`, avisos, cancelación y progreso reutilizados). Se leen las imágenes con texto, se ignoran logos/iconos por tamaño, y el texto reconocido ocupa el lugar de la imagen.
- **Texto alternativo conservado**: si la imagen trae una descripción real (`descr`/alt text) y es relevante o aporta texto, se emite como línea en cursiva junto al texto OCR; los nombres automáticos ("Imagen 3", "image.png") y las descripciones de iconos pequeños (títulos de stock copiados de la web) se descartan.
- **Salida limpia**: desaparecen las referencias rotas (`![..](X.jpg)`, `![](data:...)`).
- **Sin regresión sin imágenes**: un DOCX/PPTX sin imágenes se convierte exactamente igual que hoy (se delega en `convert_document`).
- **Degradación elegante**: una imagen que falla no aborta el archivo; se registra un aviso (`image_failed`, con la diapositiva en PPTX). Las imágenes en formatos que Pillow no abre (EMF, WMF…) se cuentan en un aviso agregado (`images_skipped`).
- **Refactor sin cambio de comportamiento**: la carga/normalización de imágenes y la lectura con reintento de orientación pasan a módulos compartidos que usan imágenes sueltas, PDFs y Office.
- **`.doc` y `.ppt` rechazados con mensaje claro** ("Formato antiguo: guárdalo como .docx/.pptx") al seleccionarlos, y como error con código estable en el sidecar si llegaran igualmente. No se implementa conversión de formatos binarios antiguos.
- **Build/CI/docs**: `markitdown` fijado a una versión concreta (hoy sin fijar y el CI instala desde git main), smoke test con un DOCX y un PPTX con imagen, specs y README al día.

Sin cambios de protocolo ni de Rust: se reutiliza `file_result.payload.warnings`.

**Cambio de salida deliberado** (único): un DOCX/PPTX *con* imágenes deja de contener las líneas `![..](..)` y pasa a contener el texto reconocido y el alt text.

## Capabilities

### New Capabilities

- `docx-image-ocr`: imágenes dentro de DOCX → texto en su posición, filtrado por tamaño, alt text, ruta rápida sin imágenes, límites y avisos.
- `pptx-image-ocr`: imágenes dentro de PPTX (incluidas las de grupos) → texto en la posición de la imagen, filtrado por área de diapositiva, alt text, ruta rápida, avisos con número de diapositiva.
- `ocr-shared-recognition`: carga de imágenes desde bytes y lectura con reintento de orientación como módulos compartidos, sin regresión para imágenes sueltas y PDFs.
- `office-conversion-diagnostics`: códigos y mensajes ES/EN nuevos (`image_failed`, `images_skipped`, `legacy_format`), progreso y cancelación por imagen.
- `legacy-office-rejection`: rechazo claro de `.doc` y `.ppt` en frontend y sidecar.

### Modified Capabilities

<!-- Ninguna en formato OpenSpec: los specs vigentes son los .md planos de openspec/specs/ (01, 05, 06, 08, 10)
     y las capacidades del change add-ocr-image-pdf-support, aún sin archivar. Al archivar hay que reflejar las
     diferencias en los .md planos (ver tasks.md, grupo 6). -->

## Impact

- **Sidecar**: nuevo `ocr/office_images.py` (docx/pptx), `ocr/image_loader.py` y `ocr/recognize.py` (extraídos de `image_converter.py` y `pdf_pipeline.py`); `main.py` (despacho por extensión `.docx`/`.pptx`, igual que `.pdf`), `error_messages.py`, `requirements.txt` (fijar `markitdown`), `smoke_test.py`, tests y fixtures.
- **Frontend**: `src/types/index.ts` (`LEGACY_EXTENSIONS`, `doc`/`ppt` fuera de `DOCUMENT_EXTENSIONS`), `fileUtils.ts`, `useConversionStore` (error de validación `legacy_format`), `ValidationErrorToast`, i18n ES/EN.
- **Rust**: sin cambios.
- **Dependencias nuevas**: ninguna (`mammoth`, `python-pptx` y Pillow ya viajan con `markitdown[all]`).
- **Acoplamiento a markitdown** (riesgo asumido): se reutiliza `markitdown.converter_utils.docx.pre_process.pre_process_docx` (ecuaciones) y el marcador `<!-- Slide number: N -->`; de ahí fijar la versión y cubrirlo con tests.
- **Instalador/arranque**: sin cambio de tamaño; las importaciones de OCR siguen siendo perezosas.
- **Docs**: README, CONTRIBUTING, specs planos 01/05/08/10 y `THIRD_PARTY_NOTICES.md` solo si cambian dependencias (no previsto).
- **Prerrequisito**: `add-ocr-image-pdf-support` (motor, layout, diagnósticos, protocolo de `warnings`). Reutiliza su código ya integrado en esta rama.
