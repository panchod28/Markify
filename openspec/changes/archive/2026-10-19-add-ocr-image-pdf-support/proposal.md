## Why

Markify solo convierte formatos con texto "nativo". Una imagen (PNG/JPG…) o un PDF escaneado hoy termina en el error "No se encontró texto en el archivo" (`sidecar/converter.py` lanza `ValueError` cuando markitdown devuelve vacío), así que justo los documentos que más necesitan pasar a Markdown para un LLM no se pueden usar. Un OCR 100 % local cierra ese hueco sin romper la promesa *local-first* de la app.

## What Changes

- **Imágenes → Markdown**: nueva categoría de archivo `image` (png, jpg/jpeg, webp, bmp, tif/tiff) convertida con OCR local en el sidecar.
- **PDFs por página**: el sidecar clasifica cada página (texto / escaneada / mixta) y aplica el tratamiento adecuado. Un PDF 100 % texto sigue el camino actual (markitdown) sin ningún cambio de salida.
- **Degradación elegante**: una página que falla (render, OCR) no aborta el archivo; se registra como *warning* con archivo/página/etapa y el `.md` sale con el resto.
- **Motor OCR detrás de una interfaz mínima** (`OcrEngine`), implementación inicial RapidOCR + ONNX Runtime con modelos PP-OCR PP-OCRv5 mobile + reconocedor `latin` para español + inglés, sin clasificador de línea), empaquetados dentro del instalador (sin descarga en primer arranque).
- **Errores estructurados y trazables** (`ConversionError` con `code`, `stage`, `file`, `page`) y log a stderr con ese contexto.
- **Protocolo sidecar ↔ frontend, solo aditivo**: `file_result.payload.warnings` opcional y progreso por página. Rust reenvía el payload tal cual, no requiere cambios.
- **UI mínima**: categoría `image` (extensiones, icono, i18n ES/EN) e indicador discreto de "completado con avisos" en la lista de resultados.
- **Build/CI**: dependencias OCR en `requirements.txt` y en el workflow, `--add-data` de los modelos en `build.py`, job de tests y *smoke test* del binario empaquetado en macOS y Windows.

Sin cambios **BREAKING**: todos los formatos y mensajes existentes se conservan.

## Capabilities

### New Capabilities

- `ocr-engine`: interfaz `OcrEngine`, implementación RapidOCR/ONNX, idiomas ES/EN, modelos locales, inicialización perezosa, punto de extensión para motores futuros.
- `image-conversion`: imagen → Markdown con OCR (formatos, orientación EXIF, límites de tamaño, orden de lectura, filtrado por confianza).
- `pdf-page-pipeline`: clasificación y tratamiento por página (texto, escaneada, mixta, en blanco), ruta rápida sin regresión para PDFs de texto, cancelación y progreso por página.
- `conversion-diagnostics`: `ConversionError`, `PageIssue`/warnings, códigos estables, log trazable, mapeo a mensajes ES/EN y campo `warnings` del protocolo.
- `ocr-packaging`: dependencias, modelos incluidos offline, PyInstaller, CI Mac/Windows, presupuesto de tamaño y arranque.
- `image-input-ui`: categoría `image` en tipos/dropzone/iconos/i18n e indicador de avisos de conversión.

### Modified Capabilities

<!-- Ninguna en formato OpenSpec: los specs vigentes son los .md planos de openspec/specs/ (01, 05, 06, 08, 10).
     Al archivar este change hay que reflejar las diferencias en esos archivos (ver tasks.md, tarea 5.2). -->

## Impact

- **Sidecar** (`sidecar/`): nuevo paquete `ocr/` (engine, layout, imágenes, pipeline PDF, diagnósticos); `main.py` (rama `image`, progreso, `warnings`), `converter.py` (ruta rápida intacta), `error_messages.py` (lookup por `code`), `build.py`, `requirements.txt`, tests.
- **Frontend**: `src/types/index.ts`, `src/lib/fileUtils.ts`, `FileIcon`, `ResultFileItem`/`ProcessingFileItem` (indicador), `useConversionStore._handleFileUpdate` (campo `warnings`), `i18n/locales/{es,en}`.
- **Rust**: sin cambios (`FilePayload.category` es `String`; los eventos reenvían `payload` sin parsear).
- **Dependencias nuevas** (a medir en el spike): `rapidocr` (Apache-2.0), `opencv-python-headless<4.13`, `pyclipper`, `shapely`; `pypdfium2` (BSD/Apache, ya llega vía `pdfplumber` de `markitdown[pdf]`, se fija explícito). `onnxruntime` ya se distribuye por `magika`. **No** se usa PyMuPDF (AGPL, incompatible con la licencia MIT del proyecto).
- **Instalador**: aumento medido ≈ 110–130 MB sin comprimir sobre un sidecar actual de ~238 MB (cv2 ≈ 99 MB, modelos 12.7 MB); además `import cv2` agrava el arranque de `--onefile` (ver design.md, Resultados del spike y Open Question 7).
- **Docs**: README, CONTRIBUTING, specs 01/05/10.
- **Prerrequisito**: change `sidecar-onedir` (el `import cv2` congelado en `--onefile` cuesta ~15 s en cada arranque).
