## Context

### Lo que hay hoy (verificado en el repo y en markitdown 0.1.6)

- **Despacho**: `sidecar/main.py::handle_convert` manda `.pdf` a `ocr.pdf_pipeline.convert_pdf` y el resto de `document` a `convert_document` (markitdown). Es el patrón a repetir para `.docx` y `.pptx`.
- **DOCX en markitdown** (`_docx_converter.py`): `pre_process_docx(stream)` (convierte ecuaciones OMML a LaTeX) → `mammoth.convert_to_html(...)` → `HtmlConverter.convert_string(html)`. Las imágenes salen como `![alt](data:image/png;base64...)`: `_markdownify.py` recorta los data-URI (`keep_data_uris=False`). El texto de la imagen no se extrae.
- **PPTX en markitdown** (`_pptx_converter.py`): recorre las formas ordenadas por `(top, left)` con recursión en grupos; cada imagen se emite como `![{alt}]({Nombre}.jpg)` y el texto alternativo cae a `shape.name` ("Picture 3") cuando no hay `descr`. Cada diapositiva empieza con `<!-- Slide number: N -->` y sus notas van en `### Notes:`. Hay un gancho `llm_client` para subtitular imágenes, pero devuelve texto dentro del alt (se aplana a una línea): no sirve para texto OCR.
- **`.doc` / `.ppt`**: son binarios OLE; markitdown lanza `UnsupportedFormatException` ("Error inesperado al convertir el archivo" en la UI). `converter.py` no ha cambiado desde el commit inicial, así que no es una regresión.
- **Lo reutilizable del change anterior**: `OcrEngine`/`get_engine()`, `layout.lines_to_markdown`, `ConversionError`/`PageIssue`/`log_issue`, `issue_to_payload`, `file_result.warnings`, el hook de cancelación y `on_progress`, y la lógica de carga de imagen de `image_converter.py` y de lectura con orientación de `pdf_pipeline.py` (hoy privadas a cada módulo).
- **Validación en el frontend**: `useConversionStore` rechaza extensiones no soportadas con un error de tipo `unsupported` que muestra `ValidationErrorToast` (`errors.unsupportedFormat`).

### Restricciones

100 % local, misma calidad en Mac y Windows, sin dependencias nuevas, `print()` prohibido en el sidecar, stdout solo JSON, importaciones de OCR perezosas, y los DOCX/PPTX sin imágenes no pueden cambiar.

## Goals / Non-goals

**Goals**
- Texto de las imágenes de DOCX/PPTX en el `.md`, en el lugar de la imagen, con alt text real conservado.
- DOCX/PPTX sin imágenes: salida idéntica byte a byte.
- Una imagen problemática no tumba el archivo; todo fallo lleva código, etapa y diapositiva.
- Reutilizar el motor y los módulos del change anterior sin cambiar su comportamiento.
- `.doc`/`.ppt` rechazados con un mensaje que diga qué hacer.

**Non-goals** (ver "Fuera de alcance")
- Convertir `.doc`/`.ppt`, OCR en XLSX/HTML/EPUB, reconstruir tablas o layout desde imágenes, descripciones de imágenes con LLM, SmartArt/WordArt/formas con relleno de imagen, recortes y giros aplicados a la imagen dentro del documento.

## Decisions

### D1. Despacho por extensión en `main.py`, igual que `.pdf`

`.docx` → `ocr.office_images.convert_docx(...)`, `.pptx` → `convert_pptx(...)`; el resto de documentos no cambia. Ambas funciones tienen la firma de `convert_pdf` (`path, cancel_flag, on_progress, engine=None -> ConversionResult`). Antes de hacer nada miran el ZIP (`word/media/*`, `ppt/media/*`): **sin imágenes → `convert_document(path)` tal cual** (ruta rápida, el motor no se carga).

*Descartado*: registrar convertidores propios en `MarkItDown` por prioridad. Mezcla la política de OCR con el registro interno de markitdown, oculta el flujo y es más difícil de probar.

### D2. DOCX: gancho de imagen de mammoth, texto en su posición

Se repite la secuencia de markitdown (`pre_process_docx` → mammoth → `HtmlConverter.convert_string`) cambiando solo el tratamiento de imágenes: `mammoth.images.img_element(callback)`. El callback recibe los bytes, el `content_type` y el `alt_text`, **en orden de documento** (verificado en el spike). Devuelve un marcador `src="markify-img:N"`; el texto OCR se guarda en un diccionario y, antes de pasar el HTML a markitdown, cada `<img src="markify-img:N">` se sustituye por `<p><em>alt</em></p><p>texto</p>` (o se elimina si no hay nada). Así el texto queda exactamente donde estaba la imagen, también dentro de tablas y listas, y se conservan las ecuaciones y todo lo demás tal y como lo hace markitdown.

`pre_process_docx` es una función interna de markitdown. Si el import falla o la conversión propia lanza un error inesperado antes de procesar imágenes, se cae a `convert_document` (ruta estable, sin OCR) con un aviso en stderr. Se fija la versión de markitdown (D10) y un test comprueba que `pre_process_docx` se invoca.

### D3. PPTX: copia en memoria con cada imagen sustituida por un cuadro de texto

Se abre la presentación con `python-pptx`, y **cada forma imagen** (imagen suelta, marcador de posición con imagen, o dentro de un grupo, recursivamente) se **sustituye por un cuadro de texto en las mismas coordenadas** que contiene el alt text real en cursiva (`*alt*`) y el texto OCR. La copia se guarda en un `BytesIO` y se convierte con markitdown como siempre. Como markitdown ordena las formas por `(top, left)` y recorre los grupos, el texto OCR aparece **en la posición de la imagen** —mejor que el "agrupado por diapositiva" acordado, sin coste añadido— y no hay que analizar la salida de markitdown ni depender de sus enlaces rotos. Solo se depende del comportamiento ya conocido de ordenar por posición. Guardar la copia cuesta ~0.2 s con un PPTX de 14 MB (medido).

Las imágenes sin texto ni alt desaparecen (no queda un cuadro vacío). Una forma con `top` heredado (`None`) usa `0`.

*Descartado*: (a) post-procesar la salida y quitar los `![..](X.jpg)` con una expresión regular, que acopla a un formato interno y obliga a emparejar cada enlace con su imagen; (b) reescribir el recorrido de formas, que duplica markitdown y arriesga regresiones en PPTX sin imágenes; (c) el gancho `llm_client`, que aplana el texto en una línea dentro del alt.

### D4. Qué imágenes se leen

- **PPTX**: área de la forma ≥ `IMAGE_MIN_AREA` (5 %, la misma constante que en PDF) de la diapositiva. En un PPTX real de 19 diapositivas había 28 imágenes y solo 1 pasaba el 5 %: el filtro evita 27 inferencias inútiles.
- **DOCX**: mammoth no da el tamaño en pantalla, así que se filtra por píxeles de la imagen (`OFFICE_MIN_SIDE_PX` y `OFFICE_MIN_PIXELS`, valores iniciales por calibrar en el spike con un corpus de capturas, logos y banners).
- Se deduplican imágenes idénticas (hash de los bytes): el mismo logotipo repetido no se lee varias veces.
- Imágenes que Pillow no abre (EMF, WMF, SVG sin respaldo): no se leen y cuentan en un único aviso `images_skipped`. En PPTX `shape.image` ya devuelve el PNG de respaldo de un SVG.
- El alt text se conserva **siempre que sea una descripción real**, también en imágenes pequeñas, y se descarta si coincide con el nombre de la forma, parece un nombre de archivo (`.png`, `.jpg`…) o es un nombre automático del tipo "Picture 3"/"Imagen 3".

### D5. Cómo se lee cada imagen

Un `image_loader.load_image(fp, name)` común (extraído de `image_converter.py`): `Image.open`, límite de píxeles, EXIF, transparencia sobre fondo blanco, RGB y reducción a ≤ 1 800 px. Después `recognize.read_image(image, engine, page_like)` (extraído de `pdf_pipeline._read_upright`): si la imagen es "de página" —cubre ≥ `SCAN_COVERAGE` (50 %) de la diapositiva en PPTX, o sus dos lados ≥ `OFFICE_PAGE_LIKE_PX` en DOCX— se usa la lectura con reintento de orientación 90/180/270° y solo líneas horizontales; si no, un único OCR a 0° (una figura sin texto no debe costar cuatro inferencias). El texto sale de `lines_to_markdown` con el mismo `MIN_CONFIDENCE` y el mismo aviso agregado `low_confidence_dropped`.

El refactor deja `convert_image` y `convert_pdf` con exactamente el mismo comportamiento (los 120 tests existentes son la red).

### D6. Errores y avisos

Un único `try/except` por imagen: produce `PageIssue("image_failed", etapa, página)` (la diapositiva en PPTX, `None` en DOCX), log a stderr con archivo/etapa/código y continúa. Sin marcador en el texto (a diferencia de una página de PDF, aquí falta una figura, no una página). Si el archivo no es un ZIP válido o python-pptx/mammoth no lo abren, se deja que lo gestione `convert_document` (mismo error que hoy). Códigos nuevos: avisos `image_failed`, `images_skipped`; error `legacy_format`. Mensajes ES/EN en `WARNINGS`/`MESSAGES`; el de `image_failed` nombra la diapositiva cuando hay `page`.

### D7. Progreso y cancelación

Se cuenta el total de imágenes por leer (tras filtrar) antes de empezar; `on_progress` emite el porcentaje tras cada imagen (0–99) y `cancel_flag` se mira antes de cada imagen. En DOCX la cancelación se señala con una excepción privada desde el callback de mammoth y se traduce en devolver `""` (como `convert_pdf`).

### D8. `.doc` y `.ppt`: rechazo claro

- Frontend: `doc` y `ppt` salen de `DOCUMENT_EXTENSIONS`/`SUPPORTED_EXTENSIONS` y pasan a `LEGACY_EXTENSIONS`. La validación añade el tipo `legacy_format` (con la extensión) y `ValidationErrorToast` muestra "Formato antiguo .{{ext}}: guárdalo como .docx/.pptx" (ES/EN). El diálogo de selección deja de ofrecerlos, pero un archivo arrastrado se rechaza con ese mensaje y no con el genérico.
- Sidecar: defensa en profundidad. Si un `.doc`/`.ppt` llegara a `handle_convert`, falla con `ConversionError("legacy_format")` y el mismo mensaje.
- `.xls` **sí** funciona (xlrd) y se mantiene.

*Descartado*: LibreOffice headless (+300–400 MB y un componente por plataforma), parsers propios de OLE (solo texto, frágiles, mucho mantenimiento), `textutil` (solo Mac) y `antiword` (GPL, solo texto, binarios por plataforma). Ver análisis en la conversación del change.

### D9. Salida deliberadamente distinta (único cambio de contenido)

Con imágenes, la salida pierde las líneas `![..](data:...)`/`![..](X.jpg)`, que no sirven a ningún lector, y gana el alt text real y el texto OCR. Sin imágenes, la salida no cambia. El resto del contenido (texto, tablas, notas, gráficos) sale igual porque lo sigue produciendo markitdown.

### D10. Empaquetado y versión de markitdown

Sin dependencias nuevas. `requirements.txt` pasa a `markitdown[all]==<versión probada>` (hoy sin fijar) y el CI/README instalan esa misma versión en vez de git main; el hook de PyInstaller ya recoge `markitdown` completo. Las importaciones de `mammoth`, `pptx` y del OCR son perezosas dentro de `office_images.py`.

## Estrategia de pruebas

1. **Unitarias puras**: alt text real vs automático, umbral de área/píxeles, deduplicación, mapeo de códigos a mensajes ES/EN, orden de sustitución.
2. **Integración con motor *fake***: orquestación DOCX y PPTX (imágenes en distintas posiciones, dentro de tabla/grupo, solo imagen, sin imágenes), imagen que explota, imagen ilegible, todas fallan (el archivo sigue saliendo con su texto), cancelación a mitad, progreso, formatos no abribles.
3. **No regresión**: DOCX/PPTX sin imágenes → `convert_office == convert_document` byte a byte; con imágenes → igual a markitdown salvo las líneas de imagen; `convert_image` y `convert_pdf` sin cambios tras el refactor (suite existente).
4. **OCR real** (`-m ocr`): DOCX y PPTX con captura con tildes, con diagrama y con página escaneada completa y girada.
5. **Frontend** (vitest): `getFileCategory`, extensiones, `legacy_format`, claves i18n.
6. **Smoke del binario**: un DOCX y un PPTX con imagen por stdin.

**Corpus** (generado por script, nada binario commiteado salvo que no se pueda generar):

| Caso | Esperado |
|---|---|
| DOCX/PPTX solo texto | Idéntico al actual (ruta rápida) |
| Texto + captura con texto | Texto nativo + texto OCR en la posición de la imagen, sin enlaces rotos |
| Solo una imagen (documento escaneado pegado) | Texto OCR; sin avisos |
| Imagen con alt text real / nombre automático | Alt en cursiva / descartado |
| Logos e iconos (pequeños) y la misma imagen repetida | Sin OCR |
| Imagen dentro de tabla (DOCX) / grupo (PPTX) / marcador con imagen | Texto en su posición |
| Imagen girada 180° a página completa | Texto legible |
| Imagen corrupta / formato no soportado (EMF) | Aviso, resto del archivo OK |
| PPTX real de 19 diapositivas y 28 imágenes | Solo se lee 1; tiempo ≈ sin OCR + 1 inferencia |
| `.doc`/`.ppt` arrastrados | Mensaje "Formato antiguo…"; el resto del lote sigue |

**Criterios de aceptación globales**: 0 diferencias en DOCX/PPTX sin imágenes; CER ≤ 5 % en capturas limpias ES/EN; ningún DOCX/PPTX del corpus termina en fallo total por una imagen; cancelación en menos de una imagen; un PPTX de 50 diapositivas con imágenes decorativas no se hace más lento que hoy de forma apreciable (el filtro evita el OCR).

## Resultados del spike (macOS arm64, 2026-10-17, antes de implementar)

| # | Hallazgo | Evidencia | Efecto en el diseño |
|---|---|---|---|
| S1 | mammoth entrega bytes, tipo y alt text en orden de documento | DOCX de prueba: 2 callbacks `('image/png', 30729, 'Captura del sistema')`, `('image/png', 156, None)` | D2 |
| S2 | markitdown deja `![alt](data:image/png;base64...)` en DOCX | salida actual del mismo DOCX | D9 |
| S3 | markitdown deja `![alt](Nombre.jpg)` en PPTX y el alt cae a `shape.name`; python-pptx rellena `descr` con el nombre del archivo ("image.png") al insertar | PPTX de prueba: `![image.png](Picture3.jpg)` | D4: filtrar alt automático |
| S4 | PPTX real (19 diapositivas, 13.9 MB): 28 imágenes (27 < 5 % de la diapositiva), 3 grupos, 7 tablas, medios `.jpeg/.jpg/.png/.svg` | recuento con python-pptx | D4: el umbral de área es imprescindible |
| S5 | Cargar 0.01 s, guardar copia 0.20 s, markitdown 0.07 s con ese PPTX | cronometrado | D3 es barato |
| S6 | `converter.py` no cambió desde el commit inicial; `.doc` binario real → `UnsupportedFormatException` | `git log`, conversión directa | D8: no es regresión |

**Por calibrar en la Fase 0**: `OFFICE_MIN_SIDE_PX`/`OFFICE_MIN_PIXELS`/`OFFICE_PAGE_LIKE_PX` en DOCX, coste real de un DOCX con muchas imágenes, comportamiento con EMF/WMF y con imágenes recortadas/rotadas, y Windows.

## Risks / Trade-offs

- **[Acoplamiento a markitdown]** (`pre_process_docx` interno; ordenar por `(top, left)` en PPTX) → versión fijada, tests que fallan si cambia, y caída a `convert_document` ante un error inesperado en DOCX.
- **[Tiempo en documentos con muchas imágenes]** → filtro por tamaño, deduplicación, progreso por imagen y cancelación entre imágenes; sin *timeout* por imagen (ONNX no es interrumpible), igual que en PDF.
- **[Falsos positivos de tamaño en DOCX]** (un banner grande sin texto se lee en balde) → cuesta tiempo, no corrección; calibrar umbrales con el corpus.
- **[Alt text automático que se cuela]** → heurística documentada y probada; lo peor es una línea de ruido.
- **[Imágenes recortadas o giradas por el documento]** (`srcRect`, `rot`) → la imagen se lee sin aplicar el recorte/giro; una imagen girada 90° se cubre solo si es "de página" (reintento de orientación). Límite documentado.
- **[Cambio de salida con imágenes]** → deliberado y documentado; los consumidores que dependieran de las líneas `![..](..)` (ninguno conocido) se verían afectados.
- **[Refactor de módulos ya integrados]** → cubierto por la suite existente (120 tests) y por la no-regresión de imágenes y PDF.
- **[Pillow no abre EMF/WMF en Windows ni Mac]** → aviso agregado `images_skipped`; fuera de alcance rasterizarlos.

## Migration Plan

Por fases, cada una liberable y con la app funcional (ver `tasks.md`): **0** spike de calibración → **1** refactor compartido sin cambio de comportamiento → **2** DOCX → **3** PPTX → **4** rechazo de `.doc`/`.ppt` → **5** empaquetado, CI y smoke → **6** documentación y cierre. Rollback: cada fase es aditiva; si falla la ruta de Office se quita la rama en `main.py` y vuelve el comportamiento actual (markitdown directo).

## Fuera de alcance

Convertir `.doc`/`.ppt`; OCR en imágenes de XLSX, HTML, EPUB o dentro de PDFs incrustados en Office; reconstruir tablas desde imágenes; descripciones de imágenes con LLM; SmartArt, WordArt, gráficos como imagen y formas con relleno de imagen; encabezados y pies de página de DOCX (mammoth no los emite); aplicar recortes/giros del documento; motores OCR alternativos; Linux e Intel Mac.

## Decisiones tomadas (acordadas con el usuario antes de abrir el change)

1. `.doc` y `.ppt` se **rechazan** con un mensaje claro; no se implementa su conversión.
2. El **alt text se conserva** (solo si es una descripción real).
3. En PPTX basta con el texto por diapositiva; este diseño lo mejora colocándolo en la posición de la imagen sin coste extra.
4. Alcance: **solo DOCX y PPTX** (con PDF, los formatos más usados).

## Open Questions

Supuestos tomados por defecto (revisables en la revisión del change):

1. **Formato del alt text**: línea en cursiva (`*texto*`) antes del texto OCR. Alternativa: sin cursiva.
2. **Imágenes pequeñas con alt text real**: se emite el alt text aunque no se lea la imagen. Alternativa: ignorarlas por completo.
3. **Marcador de imagen fallida en el texto**: ninguno (solo aviso). Alternativa: `<!-- Markify: imagen no se pudo procesar -->` como en las páginas de PDF.
4. **Umbrales de DOCX**: se calibran en la Fase 0; no se fijan a ciegas.
