> Entrega por fases. Cada fase termina con la app funcional, los tests anteriores en verde y puede liberarse sola.
> **Fase 0** es un spike descartable que decide go/no-go y fija umbrales y presupuesto. No se mergea código de producto en ella.

## 1. Fase 0 — Spike de viabilidad (sin código de producto)

- [x] 1.1 Crear venv aislado con `rapidocr`, `onnxruntime`, `opencv-python-headless<4.13`, `pypdfium2`, `pdfminer.six` y reunir el corpus mínimo (texto, escaneado ES/EN, mixto, 2 columnas, rotado, baja calidad, cifrado, corrupto)
- [x] 1.2 Medir calidad ES/EN (CER) comparando reconocedor `latin` vs `en/ch` por defecto; confirmar tildes, ñ, ¿ ¡
- [x] 1.3a Medir tiempo por página y memoria pico en Apple Silicon (hecho: 150 DPI, 1.5 s/pág, 1.4 GB)
- [ ] 1.3b Repetir en Windows (runner CI o VM)
- [x] 1.4 Confirmar que `pypdfium2` llega como dependencia de `markitdown[pdf]`/`pdfplumber` y que el venv de CI lo incluye
- [x] 1.5a Prototipo PyInstaller OCR-only en mac arm64 (onefile y onedir): OCR offline OK, tamaños y arranque medidos
- [ ] 1.5b Prototipo con el sidecar completo (markitdown + whisper + magika + OCR) en mac arm64 y Windows (CI temporal)
- [x] 1.6 Calibrar umbrales de `classify_page` (`MIN_TEXT_CHARS`, `SCAN_COVERAGE`, `IMAGE_MIN_AREA`) y `MIN_CONFIDENCE` sobre el corpus
- [x] 1.7a Informe parcial y `design.md` actualizado con cifras reales (sección "Resultados del spike")
- [x] 1.7b Decisión sobre `--onedir`: change aparte `sidecar-onedir` (prerrequisito de la Fase 1)
- [ ] 1.7c Cierre del go/no-go tras Windows y tras integrar `sidecar-onedir`
- [ ] 1.8 Validar calidad con 5–10 escaneos/fotos reales ES/EN (el corpus del spike es sintético) y ordenación de 2 columnas

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
- [ ] 2.14 Verificación manual en Mac y Windows (VM limpia): instalar, abrir, convertir PNG/JPG ES y EN sin red; confirmar no regresión de PDF/DOCX/audio. *Hecho en macOS desde la UI (`.app` con el sidecar nuevo): 6 imágenes (PNG/JPG/TIFF) → 4 convertidas (texto en español con acentos, ñ, ¿ ¡ correcto; TIFF de 3 fotogramas con icono de aviso y tooltip "Completado con avisos · Solo se procesó el primer fotograma (2 omitidos)") y 2 errores con mensaje claro (imagen corrupta, sin texto); el smoke test del sidecar sigue pasando para CSV. **Falta**: Windows, red desconectada real a nivel de sistema, y repetir PDF/DOCX/audio desde la UI tras este change*
- [ ] 2.15 Release interno de Fase 1

## 3. Fase 2 — PDFs escaneados y ruta híbrida (liberable)

- [ ] 3.1 Crear `ocr/page_classifier.py` (`classify_page` pura, constantes calibradas) + tabla de tests de casos y fronteras
- [ ] 3.2 Crear `ocr/pdf_pipeline.py`: apertura con pypdfium2, medición de métricas por página, errores fatales (`pdf_encrypted`, `pdf_open_failed`, 0 páginas)
- [ ] 3.3 Ruta rápida: todo TEXT/BLANK → `convert_document` sin cambios; test de igualdad byte a byte con varios PDFs de texto
- [ ] 3.4 Ruta híbrida: texto de página con pdfminer, página SCANNED con render (≤ 2 600 px, una página en memoria) + OCR + layout, ensamblado en orden
- [ ] 3.5 Aislamiento de fallos: captura única por página, marcador `<!-- Markify: página N … -->`, `PageIssue`, regla "todas fallan → error con el primer `code`"
- [ ] 3.6 Cancelación antes de cada página y progreso por página (`on_progress`) conectado a `main.py` (`file_progress` sin `warnings`)
- [ ] 3.7 `converter.py`/`main.py`: los `.pdf` pasan por `convert_pdf`; el resto de documentos no cambia
- [ ] 3.8 Tests con motor *fake*: mezcla de clases, página que explota, todas explotan, cancelación a mitad, progreso, PDF vacío/0 páginas, cifrado
- [ ] 3.9 Tests OCR reales (`-m ocr`) sobre escaneados ES/EN con umbral de CER
- [ ] 3.10 Prueba de memoria/tiempo con PDF escaneado sintético de ≥ 200 páginas; ampliar el smoke test del binario con un PDF escaneado
- [ ] 3.11 Verificación manual Mac + Windows: escaneado, mixto, cifrado, ruta con acentos y espacios; sin regresión de PDFs de texto
- [ ] 3.12 Release interno de Fase 2

## 4. Fase 3 — Mixtos, rotación, baja calidad y endurecimiento

- [ ] 4.1 Páginas MIXED: detectar imágenes relevantes (área ≥ `IMAGE_MIN_AREA`, no fondo completo), renderizar recorte, OCR y añadir tras el texto nativo; sin duplicar texto
- [ ] 4.2 Tests: mixto con diagrama rotulado, mixto con solo logo (sin OCR), escaneo con capa de texto previa (sin OCR)
- [ ] 4.3 Rotación: respetar `/Rotate` de pdfium; reintento 90°/180°/270° cuando el OCR a 0° no detecta texto (elige mayor `confianza × longitud`); si ninguna funciona, warning y salida parcial
- [ ] 4.4 Documentos de 2 columnas: validar y ajustar `layout.py` con el corpus (columnas desiguales, pies de página)
- [ ] 4.5 Baja calidad: ampliación de imágenes pequeñas y umbral de confianza; verificar que nunca se emite texto bajo el umbral y que el warning agregado aparece
- [ ] 4.6 Revisión de errores de extremo a extremo: toda ruta de fallo tiene `code`, `stage`, archivo/página en log y mensaje ES/EN
- [ ] 4.7 Ajuste final de rendimiento (hilos de ONNX, DPI) con las cifras del corpus; actualizar presupuesto si cambia
- [ ] 4.8 Verificación manual completa Mac + Windows con el corpus entero; checklist de no regresión (documentos, audio/Whisper, cancelación, tema, idioma)

## 5. Fase 4 — Documentación y cierre

- [ ] 5.1 Actualizar `README.md` (formatos, OCR local, tamaño) y `CONTRIBUTING.md` (tests OCR, obtención de modelos, smoke test)
- [ ] 5.2 Actualizar specs planos: `01-types` (image), `05-sidecar-protocol` (ocr/, `warnings`), `10-build` (modelos, CI); `08-i18n` si aplica
- [ ] 5.3 Incluir avisos de licencia de RapidOCR/PP-OCR/ONNX/OpenCV/pypdfium2 en el instalador
- [ ] 5.4 Anotar en CONTRIBUTING los riesgos preexistentes detectados (`--onefile`, ruta del modelo Whisper en *frozen*) como issues separados
- [ ] 5.5 `openspec validate add-ocr-image-pdf-support --strict` y archivar el change
