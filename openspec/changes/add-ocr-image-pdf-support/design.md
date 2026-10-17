## Context

### Lo que hay hoy (verificado en el repo)

- **Arquitectura**: React/Zustand → Tauri (Rust) → sidecar Python por stdin/stdout JSON newline-delimited. Rust no interpreta el contenido: `start_conversion` reenvía `{id, path, category}` y `handle_sidecar_output` emite `payload` tal cual a `conversion:file-update` (`src-tauri/src/commands/{conversion,sidecar}.rs`). `FilePayload.category` es `String`.
- **Despacho**: `sidecar/main.py::handle_convert` hace `if category == "document" → convert_document()`, `"audio" → transcribe_audio()`. Es el punto de extensión natural. La cancelación es un `threading.Event` que solo se mira entre archivos (Whisper lo mira dos veces dentro).
- **PDFs hoy**: `converter.py` envuelve `MarkItDown().convert()`; para PDF markitdown usa pdfminer + pdfplumber (que a su vez usa pypdfium2). Texto vacío → `ValueError` → mensaje "No se encontró texto". Contraseña → `PermissionError`.
- **Errores hoy**: `error_messages.get_error_message()` mapea por nombre de excepción y *substrings* ("audio_too_short", "file_corrupted"); el usuario solo ve un mensaje genérico, el traceback va a stderr sin contexto de archivo/página.
- **Progreso**: `file_progress {fileId, status, progress}`; el store (`_handleFileUpdate`) sobrescribe `status/progress/errorMessage/markdownContent` con lo que llegue.
- **Frontend**: `FileCategory = 'document' | 'audio'`; extensiones en `types/index.ts`; `getFileCategory()` en `lib/fileUtils.ts`; el diálogo del dropzone usa `SUPPORTED_EXTENSIONS`; `FILE_ICON_MAP` + `FileIcon`.
- **Empaquetado**: `sidecar/build.py` → PyInstaller `--onefile` (binario actual ≈ 238 MB, dominado por torch/whisper) → `src-tauri/binaries/` → `externalBin`. CI (`release.yml`) solo construye **macOS arm64 y Windows x64**, instala dependencias a mano (no desde `requirements.txt`, que ni siquiera lista pdf/PIL) y **no ejecuta tests**. El modelo Whisper no va en el instalador: se descarga en el primer uso (`model_manager.py`), con una ruta "junto al binario" que en `--onefile` apunta al directorio del ejecutable, no a un directorio de datos de usuario (riesgo preexistente, ver Riesgos).
- **Ya disponible, sin coste nuevo**: `onnxruntime` (dependencia de `magika`), `numpy`, `Pillow` (`--collect-all PIL`), `pypdfium2` (transitivo de `pdfplumber`; a confirmar en el spike y fijar explícito).
- **Tests existentes**: solo `sidecar/tests/test_protocol.py` y `test_sanitizer.py` (pytest) y vitest sin tests de UI relevantes.

### Restricciones que condicionan el diseño

100 % local, Mac + Windows con la misma calidad, sin GPU, sin romper estética ni lógica existente, `print()` prohibido en el sidecar, stdout solo JSON.

## Goals / Non-Goals

**Goals**
- Imagen → `.md` y cualquier PDF → `.md`, decidiendo por página.
- PDFs de solo texto: salida **idéntica** a la actual.
- Ninguna página problemática tumba el archivo; todo fallo lleva archivo/página/etapa/código.
- OCR incluido en el instalador (offline desde el primer arranque), motor reemplazable.
- Cada fase deja la app funcional y liberable.

**Non-Goals** (ver también "Fuera de alcance")
- Reconstrucción de tablas/encabezados/layout semántico desde imágenes, escritura manual, GPU, más idiomas que ES/EN, OCR dentro de DOCX/PPTX, pedir contraseña al usuario.

## Decisions

### D1. Motor: RapidOCR + ONNX Runtime, PP-OCRv5 *mobile* (detección) + reconocedor `latin`, **sin** clasificador de línea

Encaja porque `onnxruntime` ya viaja en el sidecar (vía magika), no requiere torch ni GPU, el wheel `rapidocr` pesa ~27 MB con modelos incluidos y es Apache-2.0 (verificado en PyPI). El spike (ver "Resultados del spike") confirmó: det `ch_PP-OCRv5_det_mobile` (4.8 MB) + rec `latin_PP-OCRv5_rec_mobile` (7.9 MB) = **12.7 MB**, cubre ES y EN con un solo modelo (no hace falta selector de idioma, YAGNI) y es el mejor en memoria/acentos. El clasificador de orientación de línea (`cls`) **se desactiva**: en páginas rectas desordenaba ~1 de cada 4 líneas (CER 46 % → 0 % al apagarlo); la orientación se resuelve a nivel de página (D6). Los modelos se descargan en tiempo de build, nunca en runtime. Nota: `rapidocr` 3.10 trae por defecto PP-OCRv6 *small* multilingüe (31 MB, soporta `es`), pero consume ~2.2–2.5 GB de RAM a 150–200 DPI frente a ~1.4 GB de v5; queda como alternativa si la calidad real lo exige.

| Alternativa | Costo | Beneficio | Veredicto |
|---|---|---|---|
| Tesseract | Binario nativo + `tessdata` por plataforma, dos builds distintos, peor en fotos/baja calidad | Maduro | Descartada: más piezas por empaquetar y calidad desigual |
| Apple Vision / Windows.Media.Ocr | Dos implementaciones, binding nativo por SO (Rust o pyobjc/winrt) | 0 MB, rápidas | Descartada: viola "misma calidad en Mac y Windows" y duplica código |
| EasyOCR / PaddleOCR nativo | torch/paddle (+400 MB) | Calidad alta | Descartada: peso desproporcionado |
| Docling/Surya/VLMs | Cientos de MB + RAM + a menudo GPU | Layout y tablas | Futuro opcional detrás de `OcrEngine` |
| **RapidOCR/ONNX** | +cv2-headless (~100 MB en disco), shapely, pyclipper, 12.7 MB de modelos | Ligero, CPU, una sola ruta Mac/Win | **Elegida; validada en Mac por el spike (Windows pendiente en CI)** |

Costo real medido: `opencv-python-headless` es lo que más pesa (99 MB en disco con 4.12, 119 MB con 5.0 → fijar `<4.13`) y además es el origen del problema de arranque descrito en D10. Si el delta supera el presupuesto se evalúa llamar a ONNX directo con pre/post-procesado propio (descartado de entrada por costo de mantenimiento).

### D2. Frontera de extensión: un `Protocol` y un diccionario, nada más

```
OcrLine(text, box, confidence)          # dataclass inmutable
class OcrEngine(Protocol):
    name: str
    def recognize(self, image: "PIL.Image.Image") -> list[OcrLine]: ...
ENGINES = {"rapidocr": RapidOcrEngine}   # añadir un motor = 1 archivo + 1 línea
get_engine() -> OcrEngine                # singleton perezoso
```

Es la única abstracción "de futuro" y está pedida explícitamente; cuesta ~15 líneas. **No** se crean fábricas abstractas, inyección de dependencias ni sistema de plugins: `get_engine()` lee una constante (con override por variable de entorno solo en dev). Los consumidores (`image_converter`, `pdf_pipeline`) reciben el motor por parámetro con valor por defecto `get_engine()`, lo que basta para testear con un motor *fake*.

### D3. Módulos del paquete `sidecar/ocr/` (una responsabilidad cada uno)

```
sidecar/ocr/
  engine.py            OcrLine, OcrEngine, ENGINES, get_engine()
  rapidocr_engine.py   Adaptador RapidOCR (carga perezosa, rutas de modelos)
  resources.py         resource_path(): sys._MEIPASS en frozen, repo en dev
  layout.py            lines_to_markdown(): orden de lectura, columnas, párrafos (función pura)
  page_classifier.py   classify_page(): función pura sobre métricas → PageKind
  pdf_pipeline.py      convert_pdf(): orquesta clasificación → texto/OCR → ensamblado
  image_converter.py   convert_image(): carga, EXIF, límites, OCR → layout
  diagnostics.py       ConversionError, PageIssue, log_issue()
```

Las funciones puras (`layout`, `page_classifier`) concentran la lógica con más riesgo de bugs y se testean sin OCR ni PDFs. El I/O (pdfium, ONNX) queda en bordes finos. `main.py` solo añade una rama `image` y reenvía `warnings`; `converter.py` conserva `convert_document` intacto (se reutiliza como ruta rápida).

### D4. PDF: decisión por página con ruta rápida sin regresión

1. Abrir con **pypdfium2** (BSD/Apache; PyMuPDF queda descartado por AGPL). Contraseña requerida → `ConversionError(code="pdf_encrypted")` → mismo mensaje y `PermissionError` de hoy.
2. Para cada página medir: caracteres de texto no-blancos y área cubierta por objetos imagen (relación 0..1 de la página).
3. `classify_page` (pura):
   - **TEXT**: texto ≥ `MIN_TEXT_CHARS` y sin imágenes relevantes. Incluye *escaneos con capa de texto OCR previa*: la capa de texto manda, no se re-OCR.
   - **SCANNED**: texto < `MIN_TEXT_CHARS` y hay imagen de cobertura ≥ `SCAN_COVERAGE` (o ninguna capa de texto utilizable).
   - **MIXED**: texto ≥ mínimo **y** ≥ 1 imagen con área ≥ `IMAGE_MIN_AREA` que no es fondo de página completa.
   - **BLANK**: sin texto ni imágenes → se omite sin warning.
   Los umbrales son constantes en un único módulo, calibradas con el corpus del spike.
4. **Ruta rápida**: si todas las páginas son TEXT/BLANK → `convert_document(path)` exactamente como hoy (salida byte a byte igual). Garantiza el requisito "no cambia" sin depender de reimplementar markitdown.
5. **Ruta híbrida** (≥ 1 página SCANNED/MIXED): ensamblado por página en orden:
   - TEXT → texto de la página con `pdfminer.high_level.extract_text(page_numbers=[i])` (mismo motor que markitdown; se pierde solo la detección de tablas de pdfplumber en estos documentos, trade-off documentado).
   - SCANNED → render de la página + OCR + `lines_to_markdown`.
   - MIXED → texto nativo + OCR de cada imagen relevante (recorte renderizado de la región) añadido después del texto de esa página.
   - Páginas unidas con una línea en blanco. Una página fallida se sustituye por `<!-- Markify: página N no se pudo procesar (código) -->` y se registra un warning; el resto continúa.
6. Error fatal solo si no se puede abrir el archivo / contraseña / 0 páginas. Si tras procesar no hay ningún texto y ninguna página falló → mismo `ValueError` de hoy ("No se encontró texto").

*Alternativa descartada*: re-implementar todo el PDF por página incluso para texto → riesgo de regresión sin beneficio. *Alternativa descartada*: OCR de página completa para MIXED → duplica texto nativo y es más lento.

### D5. Recursos: una página en memoria, tamaños acotados

Render a **150 DPI** con lado mayor limitado (~1 800 px); el spike midió 1.5 s/página y RSS estable en ~1.4 GB durante 40 páginas (sin crecimiento), frente a 2.2–2.5 GB con v6 small a 200 DPI; se libera el bitmap antes de la página siguiente (nunca hay un documento completo rasterizado). Imágenes: `Image.MAX_IMAGE_PIXELS` activo → `image_too_large`; se reduce por encima de ~25 MP; EXIF `transpose`; conversión a RGB. Procesamiento secuencial en un solo hilo (coherente con el loop actual; la UI no se bloquea porque el sidecar es otro proceso). Sin *timeout* por página en v1 (ONNX no es interrumpible limpiamente): se documenta como límite conocido; la cancelación se comprueba entre páginas.

### D6. Orden de lectura y limpieza (layout.py)

Entrada: `list[OcrLine]` con cajas. Pasos: descartar líneas con `confidence < MIN_CONFIDENCE` (contadas en un warning agregado, no una por línea) → detectar columnas por huecos en la proyección horizontal → ordenar arriba-abajo dentro de cada columna → unir líneas en párrafos si el salto vertical < ~1.5× la altura mediana → trim y normalización de espacios. No se infieren encabezados ni tablas (el OCR no los conoce; heurísticas frágiles = bugs).

**Orientación (nivel página, sin `cls`)**: se OCR-ea a 0°; si no se detecta texto (o muy poco frente a lo esperable) se reintenta a 90°/180°/270° y se elige la mayor suma `confianza × longitud`. El spike mostró que una orientación equivocada produce **0 líneas** (señal inequívoca) y que RapidOCR ya lee de forma nativa un sentido de 90°; el reintento solo se paga en páginas problemáticas. Páginas con `/Rotate` se resuelven antes, en el render de pdfium.

### D7. Errores y diagnóstico trazables

- `ConversionError(code, stage, file, page=None, cause=None)` con `code` estable (`pdf_encrypted`, `pdf_open_failed`, `page_render_failed`, `ocr_failed`, `ocr_engine_unavailable`, `image_decode_failed`, `image_too_large`, `no_text_found`; códigos solo de warning: `low_confidence_dropped`, `frames_skipped`) y `stage` ∈ {`open`, `classify`, `render`, `ocr`, `layout`, `assemble`}.
- `PageIssue(page, stage, code, message)` es lo que viaja al usuario como *warning*.
- **Un único lugar captura por página** (`pdf_pipeline`); el resto deja subir la excepción. Nada de `except: pass`.
- Log a stderr, una línea por incidente: `[Sidecar][ocr] file=<nombre> page=7 stage=ocr code=ocr_failed err=<tipo>: <msg>` + traceback. Sin rutas completas ni contenido del documento (privacidad).
- `get_error_message()` mira primero `getattr(exc, "code", None)` en el diccionario ES/EN y conserva el camino por nombre de excepción para el resto (sin tocar el comportamiento existente). Los textos usan el mismo estilo que los actuales.

### D8. Protocolo: solo aditivo

- `file_progress.progress` pasa a reflejar páginas procesadas (`int(100*i/n)`), solo en la ruta híbrida/imagen; sigue siendo el mismo mensaje.
- `file_result.payload.warnings: [{page, stage, code, message}]` **opcional**; ausente = comportamiento actual. Rust lo reenvía sin cambios.
- Frontend: `ConversionProgressEvent.warnings?` y `ConversionFile.warnings?`; `_handleFileUpdate` lo copia. Ojo: ese handler sobrescribe campos con `undefined`, así que los eventos de progreso no deben llevar `warnings` ni `markdownContent`.
- Cancelación: `convert_pdf(..., cancel_flag, on_progress)` mira el `Event` antes de cada página (mismo patrón que `whisper_handler`).

### D9. UI mínima y coherente

- `FileCategory` += `'image'`; `IMAGE_EXTENSIONS`; `getFileCategory` devuelve `image`; icono `Image` de lucide en `FILE_ICON_MAP`/`FileIcon` con la misma convención de color que el resto; dropzone y validación ya iteran sobre `SUPPORTED_EXTENSIONS` (cambio automático).
- Un archivo "completado con avisos" se muestra con el estado actual de completado + un icono pequeño con `Tooltip` (Radix ya instalado) que lista las páginas afectadas; usa tokens existentes (si no hay token de aviso, texto atenuado + icono, sin color nuevo). Sin pantallas, modales ni botones nuevos.
- Alternativa descartada: añadir `image` como extensión de `document` y despachar por sufijo en el sidecar → ahorra un tipo pero rompe la semántica "categoría = herramienta" documentada en `types/index.ts`.

### D10. Empaquetado, tamaño y primer arranque

- **Modelos incluidos en el instalador** (det + rec-latin, 12.7 MB): `build.py` añade `--add-data` y `--collect-all rapidocr`; `resources.resource_path()` resuelve desde `sys._MEIPASS`. **Siempre se pasan rutas explícitas** (`Det.model_path`/`Rec.model_path`): por defecto `rapidocr` descarga los modelos a su carpeta de paquete en el primer uso (verificado); con rutas explícitas el spike corrió con la red bloqueada. Sin descarga en el primer arranque y sin tocar el flujo/modal de Whisper. Se **evita** `model_manager.get_model_path()` para esto (es una ruta pensada para datos escribibles).
- Los modelos se obtienen en CI con versión y SHA-256 fijados (`scripts`/paso de build); fallo de checksum rompe el build.
- `requirements.txt` pasa a ser fuente de verdad y el workflow instala desde él (hoy duplica la lista).
- **Presupuesto** (ajustado con el spike): delta en disco ≈ 110–130 MB sin comprimir (cv2 ≈ 99 MB, shapely 7 MB, modelos 13 MB, pdfium ya presente) → presupuesto ≤ 140 MB; arranque en frío sin OCR sin cambios (importación perezosa); carga de modelos + primer OCR ≈ 3 s **una vez dentro del proceso**; RSS pico ≤ 1.5 GB.
- **Hallazgo crítico de arranque (ver spike, S7)**: con `--onefile`, `import cv2` tarda ~15 s en el binario congelado (0.1 s sin congelar) porque macOS vuelve a verificar las librerías recién extraídas en cada ejecución; con `--onedir` solo ocurre en la primera ejecución (después 0.25 s). El sidecar actual ya tarda 41–46 s en arrancar en esta máquina. Decisión pendiente (Open Question 7).
- Windows: ONNX Runtime y OpenCV requieren el runtime de Visual C++; ya lo necesita torch (Whisper), pero se valida en una VM limpia.
- **Pre-existente, fuera de alcance, a anotar**: `--onefile` se auto-extrae a un directorio temporal en cada arranque (más modelos = más extracción) y la ruta del modelo Whisper en modo *frozen* apunta junto al ejecutable. Si el spike muestra que el arranque empeora de forma visible, la mitigación es `--onedir` como `externalBin`/recurso, a decidir aparte.

## Estrategia de pruebas

**Niveles**
1. **Unitarias puras** (rápidas, sin OCR): `classify_page` (tabla de casos y fronteras), `layout.lines_to_markdown` (columnas, párrafos, confianza), `get_error_message` con `code`, mapeo de `PageIssue`.
2. **Integración con motor *fake*** (`OcrEngine` de prueba que devuelve líneas fijas): orquestación del pipeline, página que lanza excepción → warning + resto OK, cancelación a mitad, progreso, límites.
3. **Integración con RapidOCR real** (`@pytest.mark.ocr`, corre en CI Mac+Win): CER sobre texto sintético conocido.
4. **No regresión**: PDF de texto → `convert_pdf(path) == convert_document(path)` (byte a byte) + los tests actuales de protocolo/sanitizer intactos; vitest del mapeo de extensiones/categorías.
5. **Smoke del binario empaquetado** en CI (mac y win): enviar por stdin un `convert` de una imagen y de un PDF escaneado y comprobar `file_result.completed`. Es la prueba que de verdad valida PyInstaller + modelos.

**Corpus** (fixtures pequeños, generados por script con Pillow — `Image.save(..., "PDF")` produce PDFs solo-imagen sin dependencias extra — y los pocos binarios no generables, p. ej. cifrado, comprometidos < 100 KB):

| Caso | Esperado |
|---|---|
| PDF solo texto (1 y N págs, con tabla) | Idéntico al actual (ruta rápida) |
| PDF escaneado (imagen sola) ES y EN | Texto reconocido, CER ≤ objetivo |
| Escaneo con capa de texto previa | Usa capa de texto, sin OCR |
| Mixto: texto + imagen con texto | Texto nativo + OCR de la imagen |
| Mixto: texto + logo/decoración | Sin OCR de la decoración (umbral de área) |
| 2 columnas | Orden de lectura columna a columna |
| Página rotada (/Rotate 90/180/270) y escaneo girado | Texto legible o warning, nunca crash |
| Baja calidad (ruido, baja resolución, JPEG agresivo) | Salida parcial + warning de confianza, sin crash |
| Página corrupta dentro de un PDF válido | Resto del PDF convertido + warning con página |
| PDF cifrado con contraseña de apertura | Error `PermissionError` actual |
| PDF 0 páginas / truncado | Error claro con `code` |
| Imagen enorme / bomba de descompresión | `image_too_large`, sin OOM |
| Imagen con EXIF rotado | Orientación corregida |
| PDF grande (≥ 200 págs escaneadas, sintético) | Memoria estable, cancelación < 1 página de latencia |
| Ruta con acentos/espacios en Windows | Funciona |

**Criterios de aceptación globales** (objetivos propuestos; el spike los confirma o ajusta):
- Salida de PDFs de texto: 0 diferencias vs. hoy.
- CER ≤ 5 % en texto impreso limpio ES/EN a 200 DPI; ≤ 15 % en el caso de baja calidad.
- Ningún PDF del corpus termina en fallo total salvo cifrado/ilegible por completo.
- Memoria pico del sidecar en el PDF grande sin crecimiento lineal con el nº de páginas.
- Tiempo por página escaneada ≤ ~3 s en Apple Silicon y ≤ ~6 s en un portátil Windows medio.
- Instalador abre, convierte una imagen y un PDF escaneado sin red, en Mac y Windows (VM limpia).

## Resultados del spike (Fase 0, macOS arm64, 2026-10-17)

Entorno aislado (Python 3.12, `rapidocr` 3.10.0, `onnxruntime` 1.31, `pypdfium2` 5.14, `opencv-python-headless` 4.12). Corpus **sintético** (Arial/Times, ES y EN, 200 DPI, variantes de baja calidad, pequeña, rotada 90°/180°, 2 columnas) y PDFs generados (texto, escaneado, escaneo con capa de texto, mixto, cifrado, truncado, página en blanco). Métrica: CER aproximado por coincidencia de secuencias (optimista, solo para comparar configuraciones).

| # | Hallazgo | Evidencia | Efecto en el diseño |
|---|---|---|---|
| S1 | El clasificador de línea (`cls`) **daña** páginas rectas | CER medio 8 % → 0.3 % al apagarlo; `en_arial_clean` 46 % → 0 % | `use_cls=False`; orientación a nivel de página (D6) |
| S2 | Calidad con `cls` apagado | v6 small 0.3 %, v5 latin 0.2 %, v5 en: falla acentos/baja calidad (hasta 34–42 %) | Elegido det v5 mobile + rec **latin** v5 |
| S3 | Memoria | 200 DPI: v6 small 2.2–2.5 GB, v5 latin 1.4 GB; 150 DPI v5: ~1.2–1.4 GB; v6 tiny 0.7–1.0 GB pero **no** soporta es/en oficialmente | 150 DPI, tope ~1 800 px, presupuesto ≤ 1.5 GB |
| S4 | PDF escaneado de 40 págs a 150 DPI | 1.5–1.6 s/página, RSS plano en 1 375 MB | Pipeline página a página sin crecimiento (criterio cumplido en Mac) |
| S5 | Offline | Con `socket.connect` bloqueado y rutas explícitas el OCR funciona; sin rutas, `rapidocr` descarga modelos al paquete | Rutas explícitas siempre + test con red denegada |
| S6 | Clasificación con pypdfium2 | Texto: 480 chars/0 img; escaneado: 0 chars/cobertura 1.0; escaneo con capa: 480 chars/cobertura 1.0 (→ TEXT); mixto: 1 imagen ≥ 5 % (+ logo pequeño ignorado); en blanco: 0/0 | Umbrales iniciales `MIN_TEXT_CHARS=25`, `IMAGE_MIN_AREA=0.05`, `SCAN_COVERAGE=0.5`; errores: cifrado → `PdfiumError "Incorrect password"`, truncado → `PdfiumError "Data format error"` |
| S7 | Arranque congelado | OCR-only `--onefile`: 145 MB; `import cv2` 14.5 s congelado vs 0.11 s normal; sidecar actual 41–46 s en arrancar; `--onedir`: 27 s la primera vez, 0.25 s después | Open Question 7; cv2 es el mayor coste de tamaño y arranque |
| S8 | Rotación | Orientación errónea → 0 líneas detectadas; rotando 0/90/180/270 aparece el texto con confianza 0.99 | Reintento de rotación por página (D6) |
| S9 | `pypdfium2` | Es dependencia de `pdfplumber` 0.11.10 (`markitdown[pdf]`); el `.venv` local no la tiene porque no instaló los extras PDF | Fijar explícito en `requirements.txt` |

**No cubierto por el spike (pendiente)**: Windows (tiempos, tamaño, VC++ runtime, rutas Unicode) — requiere runner Windows en CI; escaneos y fotos reales; ordenación de 2 columnas (el motor devuelve cajas utilizables, la heurística se valida en 4.4); integración completa con torch/whisper/magika en un solo binario; compatibilidad de `numpy` 2.4 con `opencv` 4.12 (el spike usó `numpy` 2.2.6).

**Veredicto técnico**: **GO** para RapidOCR/ONNX con la configuración ajustada. **Condicionado** a decidir el empaquetado (`--onedir`) y a confirmar Windows.

## Risks / Trade-offs

- **[Calidad del reconocedor `latin` en documentos reales]** → el spike solo usó texto sintético (CER ≈ 0–1 %); validar con escaneos reales antes de cerrar Fase 2. Alternativa: PP-OCRv6 small (ya empaquetado en el wheel) a costa de RAM.
- **[`cls` de línea desactivado]** → páginas con líneas realmente invertidas (raro) no se corrigen; aceptado, cubierto por el reintento de rotación de página.
- **[Arranque lento por `--onefile` + cv2]** → Open Question 7; mientras tanto la importación OCR es perezosa y se avisa por progreso.
- **[Tamaño: cv2/shapely/onnx]** → medido en Fase 0; presupuesto D10; `--exclude-module` de lo no usado; ir a `opencv-python-headless` mínimo.
- **[Colisión de ONNX/numpy con magika/whisper en PyInstaller]** → smoke test del binario en CI desde la Fase 1, antes de construir el resto.
- **[Windows: VC++ runtime, rutas no ASCII]** → VM limpia en la checklist de release; pypdfium2 ya gestiona rutas Unicode en Windows; test con ruta con acentos.
- **[Arranque y extracción de `--onefile` empeoran]** → medir; importaciones perezosas; mitigación `--onedir` fuera de este change.
- **[Heurística de clasificación falla (falsos MIXED/SCANNED)]** → umbrales centralizados + corpus; el error típico es OCR extra innecesario (lento, no incorrecto) y la capa de texto siempre tiene prioridad.
- **[OCR lento en documentos grandes]** → progreso real por página, cancelación entre páginas; sin timeout por página en v1 (límite documentado).
- **[Texto basura de OCR contamina al LLM]** → umbral de confianza + warning agregado; nunca se emite texto bajo el umbral.
- **[Cambiar de pdfplumber a pdfminer por página en la ruta híbrida]** → solo afecta documentos que ya fallaban hoy ("sin texto") o mixtos; los de solo texto no pasan por ahí.
- **[Licencias]** → rapidocr/pypdfium2/ONNX/OpenCV permisivas; modelos PP-OCR Apache-2.0; incluir avisos en el instalador (tarea explícita). Evitar PyMuPDF (AGPL).

## Migration Plan

Entrega por fases, cada una liberable y con la app funcional (ver `tasks.md`): **0** spike y decisión go/no-go → **1** imágenes + motor + empaquetado + CI → **2** PDFs escaneados y ruta híbrida → **3** mixtos, rotación, baja calidad y endurecimiento → **4** docs/specs. Rollback: cada fase es aditiva; si falla el empaquetado OCR se revierte la rama `image` y las dependencias sin afectar a documentos/audio (la importación de OCR es perezosa y los PDFs de texto no la tocan).

## Fuera de alcance

OCR de fotogramas de video; reconocimiento de escritura manual; reconstrucción de tablas, listas o encabezados desde imagen; TIFF multipágina (solo primer fotograma + aviso) y HEIC/AVIF; OCR de imágenes incrustadas en DOCX/PPTX/HTML (la interfaz `OcrEngine` permite añadirlo luego); más idiomas que ES/EN (el modelo `latin` cubre otros por añadidura pero no se prueban); GPU; motores opcionales (Docling, VLM, Tesseract) más allá de dejar la interfaz lista; solicitar contraseña al usuario; Linux e Intel Mac (hoy el CI tampoco los construye); la migración de `--onefile` a `--onedir` y la ubicación del modelo Whisper.

## Open Questions

Supuestos tomados por defecto (cámbialos en la revisión si no te convencen):

1. **Marcadores de página** en la ruta híbrida/escaneada: por defecto **ninguno** (menos tokens para el LLM). Alternativa: `<!-- página N -->`.
2. **Marcar texto proveniente de OCR** en páginas mixtas: por defecto **no**. Alternativa: citar con `> ` para distinguirlo.
3. **Encabezado en el `.md` de imágenes** (como el "# Transcripción" de audio): por defecto **sin encabezado**, solo el texto.
4. **Modelos incluidos vs. descarga bajo demanda**: por defecto **incluidos** (+15–25 MB, offline real). Descargarlos reintroduciría el problema que ya tiene Whisper.
5. **Intel Mac / Linux**: se mantiene el alcance actual del CI (Mac arm64 + Windows x64). ¿Quieres ampliarlo en este change? Por defecto no.
6. **Umbrales y objetivos numéricos**: ajustados con el spike (ver arriba); los de clasificación se recalibran con PDFs reales.
7. **`--onefile` → `--onedir`** (nuevo, surgido del spike): ¿hacemos el cambio de empaquetado como prerrequisito de este change (Rust: lanzar el ejecutable desde `resources` + `tauri.conf.json` + CI), como change aparte previo, o aceptamos ~15 s extra en el primer OCR de cada sesión? **Decidido: change aparte previo, `sidecar-onedir`** (también arregla el arranque actual de 41–46 s). Las Fases 1+ de este change empiezan cuando ese change esté integrado.
