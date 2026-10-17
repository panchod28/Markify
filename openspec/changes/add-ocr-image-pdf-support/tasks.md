> Entrega por fases. Cada fase termina con la app funcional, los tests anteriores en verde y puede liberarse sola.
> **Fase 0** es un spike descartable que decide go/no-go y fija umbrales y presupuesto. No se mergea código de producto en ella.

## 1. Fase 0 — Spike de viabilidad (sin código de producto)

- [x] 1.1 Crear venv aislado con `rapidocr`, `onnxruntime`, `opencv-python-headless<4.13`, `pypdfium2`, `pdfminer.six` y reunir el corpus mínimo (texto, escaneado ES/EN, mixto, 2 columnas, rotado, baja calidad, cifrado, corrupto)
- [x] 1.2 Medir calidad ES/EN (CER) comparando reconocedor `latin` vs `en/ch` por defecto; confirmar tildes, ñ, ¿ ¡
- [x] 1.3a Medir tiempo por página y memoria pico en Apple Silicon (hecho: 150 DPI, 1.5 s/pág, 1.4 GB)
- [ ] 1.3b Repetir en Windows (runner CI o VM)
- [x] 1.4 Confirmar que `pypdfium2` llega como dependencia de `markitdown[pdf]`/`pdfplumber` y que el venv de CI lo incluye
- [x] 1.5a Prototipo PyInstaller OCR-only en mac arm64 (onefile y onedir): OCR offline OK, tamaños y arranque medidos
- [x] 1.5b Prototipo con el sidecar completo (markitdown + whisper + magika + OCR) en mac arm64. *Es el `build.py` actual: 954 MB en disco, smoke test OK (arranque posterior 1.3–2.1 s), PDF/DOCX/audio/imagen convertidos desde la `.app`.*
- [ ] 1.5c Lo mismo en Windows (job `OCR check (manual)` de GitHub Actions, que además imprime el tamaño)
- [x] 1.6 Calibrar umbrales de `classify_page` (`MIN_TEXT_CHARS`, `SCAN_COVERAGE`, `IMAGE_MIN_AREA`) y `MIN_CONFIDENCE` sobre el corpus
- [x] 1.7a Informe parcial y `design.md` actualizado con cifras reales (sección "Resultados del spike")
- [x] 1.7b Decisión sobre `--onedir`: change aparte `sidecar-onedir` (prerrequisito de la Fase 1)
- [ ] 1.7c Cierre del go/no-go tras Windows y tras integrar `sidecar-onedir`
- [x] 1.8a Calidad sobre texto real: páginas de un documento real (licencia de 310 páginas con tipografía de ~9 pt, EN y ES) renderizadas a 200 DPI y degradadas como escáner (giro 0.6°, ruido, JPEG q45) y como foto (55 % de resolución, desenfoque, JPEG q30). CER: escáner 0.07–0.09 %, foto 0.46–0.56 %, sin avisos. Páginas densas: 3–4 s/página (por encima del objetivo de ~3 s; las de poco texto van a ~0.3 s). Dos columnas justificadas con título y pie (2 págs): CER del flujo 0.01 % **tras corregir `layout.py`**, que antes mezclaba las columnas (medianil de ~40 px y 2 líneas puente).
- [ ] 1.8b Validar con 5–10 escaneos o fotos **físicos** (escáner/cámara) ES/EN. Necesita muestras reales del usuario; no depende de Windows

## 2. Fase 1 — Núcleo OCR e imágenes (liberable)

- [x] 2.1 Crear `sidecar/ocr/diagnostics.py`: `ConversionError`, `PageIssue`, `log_issue()` (stderr, sin contenido ni rutas completas) + tests
- [x] 2.2 Ampliar `error_messages.py` con lookup por `code` (ES/EN) conservando el camino actual + tests de compatibilidad
- [x] 2.3 Crear `ocr/resources.py` (`resource_path`: `sys._MEIPASS` vs repo) + test en modo normal y simulando frozen
- [x] 2.4 Crear `ocr/engine.py` (`OcrLine`, `OcrEngine`, `ENGINES`, `get_engine()` perezoso) y `ocr/rapidocr_engine.py` (det v5 mobile + rec latin v5, `use_cls=False`, rutas explícitas, sin red; test con `socket.connect` bloqueado)
- [x] 2.5 Crear `ocr/layout.py` (`lines_to_markdown`: umbral de confianza, columnas, párrafos) + tests unitarios puros
- [x] 2.6 Crear `ocr/image_converter.py` (EXIF, RGB, límites, TIFF primer fotograma, warnings agregados) + tests con motor *fake*
- [x] 2.7 `main.py`: rama `category == "image"`, envío de `warnings` en `file_result` solo si existen; verificar que stdout sigue siendo solo JSON
- [x] 2.8 Script de obtención de modelos con versión + SHA-256 fijados; `build.py`: `--add-data`, `--collect-all rapidocr`, binarios de onnxruntime/cv2; importación OCR perezosa
- [x] 2.9 `requirements.txt` completo y acotado; `release.yml` instala desde él; añadir job/paso de `pytest` (incluye `-m ocr`) en macOS y Windows
- [x] 2.10 *Smoke test* del binario empaquetado: `smoke_test.py` convierte la imagen `tests/fixtures/ocr_hello.png` por stdin y verifica el texto (pasa en macOS, 2 imágenes en 3.6 s en total, arranque posterior 2.0 s). El paso de CI ya lo ejecuta; **el control de tamaño en CI queda pendiente** (medido local: 954 MB frente a 850 MB sin OCR, +104 MB)
- [x] 2.11 Frontend: `FileCategory 'image'`, `IMAGE_EXTENSIONS`, `getFileCategory`, `FILE_ICON_MAP`/`FileIcon` (icono lucide) + tests vitest de categorías y extensiones existentes sin cambio
- [x] 2.12 Frontend: tipos `ConversionWarning`, `warnings?` en evento y archivo, copia en `_handleFileUpdate`; i18n ES/EN de errores nuevos
- [x] 2.13 Indicador de avisos (icono + `Tooltip`) en la fila de resultados con tokens existentes; revisión visual en claro/oscuro
- [x] 2.14a Verificación manual en macOS desde la UI (`.app` con el sidecar nuevo): PNG/JPG/TIFF ES y EN, PDF, DOCX y audio (descarga del modelo Whisper desde su modal y transcripción) convertidos; sin red a nivel de SO (`sandbox-exec` con `deny network*`: imagen, PDF escaneado y mixto OK en 2.6 s); lote con ruta con acentos, ñ y espacios. *El 1.er arranque del binario nuevo tarda ~35 s (verificación del SO).*
- [ ] 2.14b Lo mismo en Windows (VM limpia): instalar, abrir, convertir PNG/JPG ES y EN sin red; PDF/DOCX/audio sin regresión
- [ ] 2.15 Release interno de Fase 1

## 3. Fase 2 — PDFs escaneados y ruta híbrida (liberable)

- [x] 3.1 Crear `ocr/page_classifier.py` (`classify_page` pura, constantes calibradas) + tabla de tests de casos y fronteras *Umbrales 25 / 0.05 / 0.5; 20 casos y fronteras. Cobertura = suma de imágenes (tope 1), imagen mayor aparte para MIXED.*
- [x] 3.2 Crear `ocr/pdf_pipeline.py`: apertura con pypdfium2, medición de métricas por página, errores fatales (`pdf_encrypted`, `pdf_open_failed`, 0 páginas) *pypdfium2 5.10; error de contraseña → `PermissionError` actual; "Data format error" y 0 páginas → `pdf_open_failed`. Una página que falla al medir se trata como SCANNED y el render decide.*
- [x] 3.3 Ruta rápida: todo TEXT/BLANK → `convert_document` sin cambios; test de igualdad byte a byte con varios PDFs de texto *`convert_pdf == convert_document` en 4 PDFs (texto, 5 págs, tabla, escaneo con capa de texto); el motor no se carga. MIXED cuenta como TEXT hasta 4.1.*
- [x] 3.4 Ruta híbrida: texto de página con pdfminer, página SCANNED con render (≤ 2 600 px, una página en memoria) + OCR + layout, ensamblado en orden *150 DPI, lado mayor ≤ 1 800 px (no 2 600), una página en memoria. CER 0.0 % en ES (tildes, ñ, ¿ ¡) y EN sobre el corpus sintético, ~0.4–0.6 s/página en este Mac.*
- [x] 3.5 Aislamiento de fallos: captura única por página, marcador `<!-- Markify: página N … -->`, `PageIssue`, regla "todas fallan → error con el primer `code`" *`PageIssue("page_failed", stage)` + marcador con el código de causa (`page_render_failed`, `ocr_failed`, `page_failed`); el spec se ajustó a esto. Avisos de baja confianza agregados en uno solo por archivo.*
- [x] 3.6 Cancelación antes de cada página y progreso por página (`on_progress`) conectado a `main.py` (`file_progress` sin `warnings`) *Progreso `100·i/n` tras cada página (tope 99); cancelación medida: 0.11 s con páginas de 0.36 s.*
- [x] 3.7 `converter.py`/`main.py`: los `.pdf` pasan por `convert_pdf`; el resto de documentos no cambia *Solo `.pdf` entra por `convert_pdf`; resto de documentos intacto.*
- [x] 3.8 Tests con motor *fake*: mezcla de clases, página que explota, todas explotan, cancelación a mitad, progreso, PDF vacío/0 páginas, cifrado *`test_ocr_page_classifier.py` + `test_ocr_pdf_pipeline.py` (motor falso): mezcla, página que explota, página ilegible, todas fallan, sin texto, cancelación a mitad y previa, progreso, cifrado, truncado, 0 páginas. Fixtures generados por `make_fixtures.py` (nada binario commiteado).*
- [x] 3.9 Tests OCR reales (`-m ocr`) sobre escaneados ES/EN con umbral de CER *Dentro de `test_ocr_pdf_pipeline.py` (`-m ocr`): CER 0.0 % (umbral 5 %) en ES y EN.*
- [x] 3.10 Prueba de memoria/tiempo con PDF escaneado sintético de ≥ 200 páginas; ampliar el smoke test del binario con un PDF escaneado *`tests/stress_pdf_memory.py`, 200 páginas: 72 s (0.36 s/pág), RSS plano (1er cuarto 1 881 MB → último 1 645 MB) y pico de 1.88 GB (> 1.5 GB) que se corrigió en 4.7 (ver allí: 1.1 GB). Smoke test del binario con PDF escaneado de 2 páginas: OK (arranque posterior 2.1 s).*
- [x] 3.11 Verificación manual en macOS (escaneado, mixto, cifrado, ruta con acentos y espacios, sin regresión de PDFs de texto): ver 4.8a.
- [ ] 3.11b Verificación manual en Windows (mismos casos, ruta con acentos y espacios)
- [ ] 3.12 Release interno de Fase 2

## 4. Fase 3 — Mixtos, rotación, baja calidad y endurecimiento

- [x] 4.1 Páginas MIXED: detectar imágenes relevantes (área ≥ `IMAGE_MIN_AREA`, no fondo completo), renderizar recorte, OCR y añadir tras el texto nativo; sin duplicar texto *`_measure` devuelve las cajas de imágenes ≥ 5 %; recorte del bitmap ya renderizado (sigue `/Rotate`); el texto OCR va tras el nativo. Si falla el OCR de la figura, se conserva el texto nativo y se añade el marcador. Coste: los PDFs con figuras ya no usan la ruta rápida (pierden la detección de tablas de pdfplumber en esas páginas).*
- [x] 4.2 Tests: mixto con diagrama rotulado, mixto con solo logo (sin OCR), escaneo con capa de texto previa (sin OCR) *`mixed_diagram` (OCR una vez, tras el texto), `mixed_logo` (idéntico a `convert_document`, 0 llamadas al motor), `scan_text_layer` (sin OCR), `mixed_diagram_rot90` y fallo de figura.*
- [x] 4.3 Rotación: respetar `/Rotate` de pdfium; reintento 90°/180°/270° cuando el OCR a 0° no detecta texto (elige mayor `confianza × longitud`); si ninguna funciona, warning y salida parcial *`/Rotate` lo resuelve pdfium (1 llamada al motor). Reintento 90/180/270° cuando a 0° no hay líneas horizontales legibles; solo cuentan líneas horizontales, porque el motor lee texto vertical con confianza ~1.0 pero con cajas que el layout no ordena (un escaneo a 180° salía desordenado). CER ≈ 0 en 90/180/270°. Una página escaneada realmente vacía pasa ahora por 4 inferencias y acaba como aviso `page_failed`/`ocr_failed`, como pide el spec.*
- [x] 4.4 Documentos de 2 columnas: validar y ajustar `layout.py` con el corpus (columnas desiguales, pies de página) *`layout.py` tolera una línea puente (título o pie centrado) al buscar el hueco entre columnas y la coloca antes/después de ellas; columnas desiguales OK. Validado con corpus sintético; falta con documentos reales.*
- [x] 4.5 Baja calidad: ampliación de imágenes pequeñas y umbral de confianza; verificar que nunca se emite texto bajo el umbral y que el warning agregado aparece *Medido: ampliar imágenes pequeñas (×2, ×3, hasta 1800 px) no mejora y a veces empeora el CER (ruido + JPEG q20 + fuentes de 12–18 px: 0.0–1.3 % sin ampliar) → no se implementa. El umbral de confianza y el aviso agregado ya están cubiertos por tests (imagen y PDF: nunca se emite texto bajo `MIN_CONFIDENCE`).*
- [x] 4.6 Revisión de errores de extremo a extremo: toda ruta de fallo tiene `code`, `stage`, archivo/página en log y mensaje ES/EN *`test_error_codes.py`: todo `ConversionError("code")` y `PageIssue("code")` del paquete OCR tiene mensaje/plantilla ES y EN; cada fallo de página se registra con archivo/página/etapa/código + traceback en stderr.*
- [x] 4.7 Ajuste final de rendimiento (hilos de ONNX, DPI) con las cifras del corpus; actualizar presupuesto si cambia *Causa del pico: `Det.limit_type=min/736` dejaba la página A4 a 150 DPI entera en el detector. Con `max/1280`: RSS pico 1 105 MB (antes 1 883), 0.31 s/pág (antes 0.36), CER sin cambio en texto de 7–10 pt (0.4–0.7 %); con 960 baja a 644 MB, pero se deja 1280 por margen con escaneos reales. Windows sin medir.*
- [x] 4.8a Verificación manual completa en macOS: escaneado/girado/mixto/figura/dos columnas/cifrado/página ilegible (marcador + icono de aviso), PDF largo con cancelación a mitad (vuelve a la lista, sidecar inactivo 0 % CPU y re-uso OK), DOCX, audio (Whisper), cambio de tema e idioma y persistencia tras reiniciar la app. *Pendiente solo cosmético: el comentario `<!-- Markify: página N … -->` se ve como texto en la vista previa renderizada.*
- [ ] 4.8b Verificación manual completa en Windows con el corpus entero y el mismo checklist

## 5. Fase 4 — Documentación y cierre

- [x] 5.1 Actualizar `README.md` (formatos, OCR local, tamaño) y `CONTRIBUTING.md` (tests OCR, obtención de modelos, smoke test) *README (formatos, OCR, límites, estructura, build) y CONTRIBUTING (tests con OCR, `fetch_ocr_models.py`, stress y smoke, ajustes). El CI de tests ahora instala también `reportlab` (los fixtures lo necesitan).*
- [x] 5.2 Actualizar specs planos: `01-types` (image), `05-sidecar-protocol` (ocr/, `warnings`), `10-build` (modelos, CI); `08-i18n` si aplica *`01-types` (image, `ConversionWarning`, extensiones, icono), `05-sidecar-protocol` (progreso por página, `warnings`, §14 OCR/PDF/errores), `08-i18n` (claves nuevas ES/EN; también añadidas a `messages.json` las de PDF), `10-build` (modelos, flags, CI, tamaño, checklist).*
- [x] 5.3 Incluir avisos de licencia de RapidOCR/PP-OCR/ONNX/OpenCV/pypdfium2 en el instalador *`THIRD_PARTY_NOTICES.md` con RapidOCR, modelos PP-OCRv5, ONNX Runtime, OpenCV, pypdfium2/PDFium, pdfminer.six, Shapely/pyclipper y Pillow; incluido en `Resources/` de la `.app` (verificado) y en `tauri.windows.conf.json` (sin verificar). Los textos completos (LICENSE/NOTICE de cada paquete) van en `THIRD_PARTY_LICENSES.txt`, generado con `sidecar/gen_licenses.py` y también incluido en ambos instaladores (verificado en la `.app`). Una revisión legal humana sigue siendo recomendable, no bloqueante.*
- [x] 5.4 Anotar en CONTRIBUTING los riesgos preexistentes detectados (`--onefile`, ruta del modelo Whisper en *frozen*) como issues separados *Sección "Known risks" en CONTRIBUTING: ruta del modelo Whisper en frozen, 1.er arranque lento, sin timeout por página, tablas de pdfplumber en PDFs mixtos, RAM en Windows sin medir. `--onefile` ya no aplica tras `sidecar-onedir`. **Falta** abrirlos como issues en GitHub.*
- [ ] 5.5 `openspec validate add-ocr-image-pdf-support --strict` y archivar el change *`validate --strict` pasa; el archivado queda pendiente hasta cerrar las tareas abiertas (2.14, 2.15, 1.3b, 1.5b, 1.7c, 1.8, 3.12, 4.8).*
