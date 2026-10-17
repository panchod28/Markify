> Entrega por fases. Cada fase termina con la app funcional, los tests anteriores en verde y puede liberarse sola.
> **Fase 0** calibra los umbrales de DOCX y mide costes; no se mergea código de producto en ella.
> Prerrequisito: `add-ocr-image-pdf-support` (motor, layout, diagnósticos y `warnings`), ya integrado en la rama.

## 1. Fase 0 — Calibración (sin código de producto)

- [x] 1.1 Corpus de DOCX: capturas de pantalla con texto, diagrama rotulado, página escaneada pegada (recta y girada 180°), logos y banners de cabecera, iconos, la misma imagen repetida, imagen en tabla, imagen con alt text real y con nombre automático, EMF/WMF *`tests/make_office_fixtures.py` (constructor de DOCX sin dependencias nuevas + 11 documentos: solo texto, captura entre párrafos, solo imagen, escaneo a 180°, iconos y logo, imagen repetida, imagen en tabla, alt automático, foto sin texto, EMF, imagen corrupta). mammoth entrega bytes, tipo y alt text de los 11 en orden de documento. Falta el corpus de DOCX reales (no hay muestras).*
- [x] 1.2 Calibrar los umbrales (`OFFICE_MIN_AREA`, `OFFICE_MIN_TEXT_CHARS` y el respaldo en píxeles) con iconos reales, fotos reales, texto corto y un PPTX real; anotar cifras en `design.md` *Cambio de criterio frente al borrador: un umbral de píxeles no separa iconos de texto pequeño (texto de 8 px legible en 149 × 22 px; el 40–60 % de 50 iconos reales de apps "leen" 1–5 caracteres basura). Se usa tamaño mostrado ≥ 1 % + deduplicación + descartar resultados de < 6 alfanuméricos; respaldo en píxeles 100 px / 20 000 px². Cifras en design.md (S7–S10).*
- [x] 1.3 Medir coste: DOCX con 30 imágenes relevantes y PPTX real de 19 diapositivas (tiempo, RSS); confirmar el orden de mammoth con imágenes en tablas y listas *PPTX real (28 imágenes): OCR de todas 1.2 s, de las 9 ≥ 1 %: 0.6 s; cargar 0.01 s y guardar copia 0.2 s. Fotos reales 3–280 ms. mammoth conserva el orden con imágenes en tabla. Falta un DOCX real con ≥ 30 imágenes relevantes y Windows.*
- [x] 1.4 Comprobar con python-pptx: sustituir una imagen por un cuadro de texto en las mismas coordenadas (suelta, marcador de posición con imagen, dentro de un grupo) y que markitdown conserve el orden de lectura; confirmar el comportamiento con `top`/`left` heredados (`None`) *Prototipo validado (S11): suelta, marcador con imagen y en grupo; en el deck real se sustituyeron 28 imágenes y la salida de markitdown fue idéntica a la original salvo las líneas de imagen. Las coordenadas heredadas de un marcador las resuelve python-pptx; si fueran `None` se usa 0.*
- [x] 1.5 Confirmar el comportamiento con EMF/WMF/SVG en Pillow (macOS y, vía CI, Windows) y con imágenes recortadas/giradas dentro del documento (límite documentado) *Pillow en macOS: EMF (mínimo) → `ZeroDivisionError`, SVG/basura → `UnidentifiedImageError`, GIF abre; por eso se decide por tipo de contenido (EMF/WMF/SVG → `images_skipped`). Recortes y giros dentro del documento no se aplican (límite documentado). Windows sin verificar (job manual `OCR check`).*
- [x] 1.6 Decidir la versión de markitdown a fijar (la probada) y comprobar que `pre_process_docx` y el marcador `<!-- Slide number: N -->` existen en ella *Se fija `markitdown[all]==0.1.6` de PyPI: su salida es idéntica a la del commit git instalado (hash igual en 13 documentos) y tiene `pre_process_docx` y el marcador de diapositiva; 0.1.8 ya cambia las líneas de imagen del PPTX real.*

## 2. Fase 1 — Módulos compartidos (refactor sin cambio de comportamiento)

- [x] 2.1 Extraer `ocr/image_loader.py` (`load_image` desde ruta o bytes: EXIF, transparencia sobre blanco, RGB, límites, ≤ 1 800 px) de `image_converter.py`, que pasa a usarlo *`ocr/image_loader.py::load_image(ruta|bytes, nombre, max_side=2000)` → (imagen RGB, nº de fotogramas). Mejora incluida: la transparencia se compone sobre blanco (antes se descartaba el alfa y el texto negro sobre fondo transparente era ilegible).*
- [x] 2.2 Extraer `ocr/recognize.py` (`read_upright` con reintento de orientación y solo líneas horizontales; `read_simple` de un único OCR) de `pdf_pipeline.py`, que pasa a usarlo *`ocr/recognize.py`: `read_simple` y `read_upright` (movido tal cual desde `pdf_pipeline`); los recortes de figuras de PDF usan `read_simple`.*
- [x] 2.3 Tests nuevos de `load_image` (bytes, transparencia, bomba de descompresión, bytes inválidos) y de `read_simple`/`read_upright` con motor falso *`test_ocr_image_loader.py` (8 tests) y `test_ocr_recognize.py` (7 tests, motor falso).*
- [x] 2.4 Verificar que la suite existente (imágenes, PDF, layout, errores) pasa sin tocar sus expectativas *Suite completa: 135 tests en verde (120 previos + 15 nuevos). Único retoque en tests existentes: dos referencias a constantes que ahora viven en `image_loader` (`MAX_PIXELS`, `MAX_SIDE_PX`); sus expectativas no cambian.*

## 3. Fase 2 — DOCX (liberable)

- [ ] 3.1 Crear `ocr/office_images.py` con utilidades comunes: alt text real (descarta nombre de archivo y nombres automáticos), deduplicación por hash, formato `*alt*` + texto, aviso agregado `images_skipped`
- [ ] 3.2 `convert_docx`: sin imágenes (`word/media/*`) → `convert_document`; con imágenes → `pre_process_docx` + mammoth con `img_element` + sustitución de marcadores + `HtmlConverter.convert_string`; caída a `convert_document` si falla la cadena propia antes de leer imágenes
- [ ] 3.3 Lectura por imagen: filtro por tamaño mostrado (`wp:extent` emparejado por SHA-1, `w:pgSz`; respaldo en píxeles), filtro de ≥ 6 alfanuméricos, `read_upright` para imágenes de página y `read_simple` para el resto, un único `try/except` por imagen con `PageIssue("image_failed", etapa)` y log a stderr
- [ ] 3.4 Progreso por imagen y cancelación (excepción privada desde el callback de mammoth → `""`)
- [ ] 3.5 `main.py`: los `.docx` pasan por `convert_docx`; el resto de documentos no cambia
- [ ] 3.6 Tests con motor falso: imagen entre párrafos, solo imágenes, imagen en tabla, sin texto ni alt (sin `![`), alt real vs automático, icono ignorado, imagen repetida (una inferencia), imagen que explota, EMF → `images_skipped`, cancelación a mitad, progreso, archivo no abrible
- [ ] 3.7 No regresión: DOCX sin imágenes `== convert_document` byte a byte (incluida una ecuación); con imágenes `==` markitdown descontadas las líneas de imagen; test de que `pre_process_docx` se invoca
- [ ] 3.8 Tests OCR reales (`-m ocr`): captura con tildes ES, diagrama, página escaneada girada 180°, con umbral de CER
- [ ] 3.9 Verificación manual macOS: DOCX real con capturas y con escaneo pegado

## 4. Fase 3 — PPTX (liberable)

- [ ] 4.1 `convert_pptx`: sin imágenes (`ppt/media/*`) → `convert_document`; con imágenes → abrir con python-pptx, recorrer formas (grupos recursivamente), clasificar cada imagen (área ≥ `OFFICE_MIN_AREA`, duplicada, tipo no soportado) y sustituirla por un cuadro de texto en las mismas coordenadas con `*alt*` y el texto OCR; guardar la copia en `BytesIO` y convertir con markitdown
- [ ] 4.2 Lectura por imagen: `read_upright` si cubre ≥ `SCAN_COVERAGE` de la diapositiva, `read_simple` si no; un único `try/except` por imagen con `image_failed` y la diapositiva; imágenes sin texto ni alt desaparecen
- [ ] 4.3 Progreso por imagen, cancelación y `main.py` (los `.pptx` pasan por `convert_pptx`)
- [ ] 4.4 Tests con motor falso: imagen suelta, marcador con imagen, imagen en grupo, diapositiva solo imagen, iconos ignorados, alt con descripción real en icono, `image.png` descartado, imagen duplicada, imagen que explota con `page=4`, cancelación, progreso, tabla y notas intactas
- [ ] 4.5 No regresión: PPTX sin imágenes `== convert_document` byte a byte; con imágenes `==` markitdown descontadas las líneas de imagen y el texto añadido
- [ ] 4.6 Tests OCR reales (`-m ocr`): captura con tildes, diapositiva escaneada girada 180°; prueba con el PPTX real de 19 diapositivas (se leen 9 imágenes, no se emite texto basura, el logotipo repetido sale una vez)
- [ ] 4.7 Verificación manual macOS: PPTX real con capturas, iconos y logos

## 5. Fase 4 — Rechazo de `.doc` y `.ppt` (liberable)

- [ ] 5.1 Frontend: `LEGACY_EXTENSIONS = ['doc','ppt']`, `doc`/`ppt` fuera de `DOCUMENT_EXTENSIONS`; error de validación `legacy_format` en `useConversionStore` y su mensaje en `ValidationErrorToast`; i18n ES/EN
- [ ] 5.2 Tests vitest: extensiones y categorías (incluido `.xls` aceptado, `.xyz` genérico), validación `legacy_format` en un lote mixto, claves i18n ES/EN
- [ ] 5.3 Sidecar: `ConversionError("legacy_format")` para `.doc`/`.ppt` en `handle_convert` + mensajes ES/EN + test
- [ ] 5.4 Verificación manual macOS: arrastrar `.doc` junto a un `.docx`; selector sin `.doc`/`.ppt`

## 6. Fase 5 — Empaquetado, CI y smoke

- [ ] 6.1 `requirements.txt`: `markitdown[all]==<versión probada>`; README/CONTRIBUTING y los workflows instalan esa versión en vez de git main; comprobar que PyInstaller sigue recogiendo `mammoth`, `pptx` y el OCR
- [ ] 6.2 `smoke_test.py`: un DOCX y un PPTX con una imagen con texto por stdin, comprobando el texto y que no quedan líneas `![`
- [ ] 6.3 Ampliar `make_regression_folder.py` con un DOCX y un PPTX con imágenes; `ocr-check.yml` ya ejecuta tests y smoke en macOS y Windows
- [ ] 6.4 Reconstruir (`python build.py`), correr `smoke_test.py` y generar el `.dmg`

## 7. Fase 6 — Documentación y cierre

- [ ] 7.1 README (formatos, OCR en DOCX/PPTX, `.doc`/`.ppt` no soportados, límites) y CONTRIBUTING (módulos compartidos, calibración de umbrales)
- [ ] 7.2 Specs planos: `01-types` (`LEGACY_EXTENSIONS`, `doc`/`ppt`), `05-sidecar-protocol` (§14: Office, `image_failed`, `images_skipped`, `legacy_format`), `08-i18n` (claves nuevas), `10-build` (versión fijada de markitdown, smoke)
- [ ] 7.3 Verificación manual completa en macOS y Windows: carpeta de regresión con todos los formatos + DOCX/PPTX con imágenes; sin regresión de PDF, imágenes, audio, cancelación, tema e idioma
- [ ] 7.4 `openspec validate add-ocr-office-images --strict` y archivar el change
