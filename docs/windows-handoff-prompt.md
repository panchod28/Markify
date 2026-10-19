# Prompt para terminar Markify en Windows

Copia el bloque de abajo como primer mensaje de una sesión nueva de Claude Code abierta en la carpeta del repo, **en el equipo con Windows 10/11 (x64)**. Antes, en ese equipo: `git clone https://github.com/panchod28/markify.git`, `git checkout develop` y, si el último commit de macOS aún no está subido, pídeselo al otro equipo (`git push origin develop`).

---

```text
Eres mi ingeniero en Markify (app de escritorio Tauri v2 + React + sidecar Python que convierte documentos/imágenes/audio a Markdown). Responde en español, directo y sin relleno. Estás en un equipo WINDOWS (x64) y tu misión es TERMINAR lo pendiente de Windows y dejarme los INSTALADORES (.msi y .exe NSIS) listos para subir al release de GitHub, con la descripción del release actualizada para marcarlo como "latest".

## Estado (todo lo de macOS está hecho y verificado)
- Rama de trabajo: `develop` (flujo: develop → merge ff a main; el release apunta a main). Versión de la app: 1.1.0; release/tag: `v1.1.0-beta` (beta). Ejecuta `git fetch` y `git log --oneline -5 origin/main origin/develop` primero: el último commit local de macOS (docs `5ee233d`, pasos de apertura en macOS 15+) puede no estar aún en el remoto.
- Nuevo en 1.1.0: OCR local (RapidOCR/ONNX, PP-OCRv5, ES/EN) para imágenes, PDFs escaneados por página, imágenes dentro de DOCX/PPTX; `.doc`/`.ppt` rechazados con mensaje claro; vista previa que oculta comentarios HTML; markitdown fijado a 0.1.6; licencias de terceros incluidas (THIRD_PARTY_NOTICES.md + THIRD_PARTY_LICENSES.txt, generado por scripts/gen_licenses.py).
- Verificado en macOS (Apple Silicon): 207 tests pytest, 16 vitest, smoke del binario (arranque posterior 1.3 s; 1.º arranque ~35 s), OCR de PDF de 200 págs con pico de RAM ≈ 1.1 GB y 0.31 s/pág, carpeta de regresión con todos los formatos, UI manual, offline real, `.dmg` de 291 MB publicado como release (macOS solo).
- El release `v1.1.0-beta` en GitHub solo tiene el `.dmg`; falta Windows. El release anterior `v1.0.0-beta` tiene el instalador viejo de Windows.

## Reglas
- NO uses GitHub Actions (los workflows `release.yml` y `ocr-check.yml` son solo manuales y no se van a lanzar). Construimos a mano.
- Nada de push/tags/PR/borrados sin pedirme confirmación en el momento. Sin force-push. Commits pequeños con el trailer de atribución que indique tu sistema.
- No cambies código de producto si no lo exige un fallo de Windows. Si un fallo obliga a tocar sidecar/frontend, PARA y pregúntame: el `.dmg` ya publicado correspondería a otro código (habría que subir a 1.1.1-beta y reconstruir también el de Mac).
- Eficiencia: empieza con la lista de tareas junto a la primera lectura; lee solo lo necesario (por rangos o grep), nunca `node_modules`, `.venv` ni logs enteros (usa `Select-Object -Last`). Esperas largas (build del sidecar ~3-5 min, `tauri build` 5-10 min, 1.er arranque del binario 30-50 s): en segundo plano y sin sleeps encadenados. No ejecutes la UI por tu cuenta: la prueba manual la hago yo con tu checklist.
- NO dejes `models\whisper\base.pt` dentro de `src-tauri\binaries\` al empaquetar (se incluiría en el instalador, +145 MB).
- Solo lo de Windows: no intentes `sandbox-exec`, `say`, `afconvert`, `textutil` ni la firma de macOS.

## Léelo antes de empezar (y nada más)
1. `openspec/changes/add-ocr-image-pdf-support/tasks.md` y `openspec/changes/add-ocr-office-images/tasks.md`: solo las líneas `- [ ]`. Las de Windows son: 1.3b, 1.5c, 1.7c, 2.14b, 3.11b, 4.8b, 2.15, 3.12, 5.5 (change OCR imágenes/PDF) y 7.3b, 7.4 (change Office). 2.15/3.12 (releases internos por fase) se sustituyen por UN solo release; 5.5/7.4 = `openspec validate <change> --strict` y archivar (`openspec archive`), al final y con mi OK.
2. `design.md` de add-ocr-image-pdf-support: "Resultados del spike", D5, D10 y "Riesgos" (presupuestos: RAM pico ≤ 1.5 GB, ≤ ~6 s/pág en portátil Windows medio, arranque posterior ≤ 3 s).
3. `CONTRIBUTING.md` (secciones "OCR and sidecar tests", "Releasing → Manual release", "Known risks"), `sidecar/build.py`, `sidecar/smoke_test.py`, `sidecar/tests/stress_pdf_memory.py`, `src-tauri/tauri.windows.conf.json`, `sidecar/model_manager.py` (ruta del modelo Whisper) y `README.md` (Download).

## Preparar el entorno (PowerShell)
Requisitos: Python 3.12, Node 20, Rust (toolchain MSVC), Visual Studio Build Tools con "Desktop development with C++", WebView2 y FFmpeg (`winget install ffmpeg`). Si falta algo, dímelo con el comando exacto.
```
py -3.12 -m venv sidecar\.venv; sidecar\.venv\Scripts\Activate.ps1
pip install setuptools==70.0.0; pip install -r sidecar\requirements.txt; pip install pytest reportlab
cd sidecar; python fetch_ocr_models.py   # modelos OCR con SHA-256 fijado (necesita internet 1 vez)
```

## Tareas, en orden
1. **Tests** (`python -m pytest -q` en sidecar; `npm ci; npm run type-check; npm test`). Esperado en macOS: 207 y 16. Investiga y clasifica cada fallo (¿entorno Windows o bug?): fuentes de `tests/make_fixtures.py` (Arial en C:\Windows\Fonts), rutas, CRLF, `tqdm`/whisper.
2. **Medidas (1.3b, 1.5c)**: `python tests\stress_pdf_memory.py 60` (RSS por ctypes, sin probar en Windows: arréglalo si falla) → pico de RAM, s/pág, latencia de cancelación; tamaño de la carpeta `src-tauri\binaries\markify-sidecar` tras `python build.py` (macOS: 954 MB en disco).
3. **Build y smoke**: `python build.py` y `python smoke_test.py --max-seconds 3` (CSV, imagen, PDF escaneado, DOCX y PPTX con imagen). Riesgos conocidos: DLL de onnxruntime/OpenCV y VC++ runtime, rutas > 260 caracteres de `_internal`, UTF-8, antivirus con falsos positivos de PyInstaller.
4. **Carpeta de regresión**: `sidecar\tests\make_regression_folder.py` solo funciona en macOS (usa `say`, `afconvert`, `textutil`, ffmpeg). Pídeme que copie al equipo la carpeta ya generada (26 archivos) o genera lo que se pueda con ffmpeg; verifica por el binario que todo convierte salvo `.doc` (debe rechazarse con "Formato antiguo…").
5. **Instaladores**: `npm run tauri build` (targets "all" → MSI con WiX y NSIS; Tauri descarga WiX/NSIS, necesita internet). Salidas esperadas: `src-tauri\target\release\bundle\msi\Markify_1.1.0_x64_en-US.msi` y `...\nsis\Markify_1.1.0_x64-setup.exe`. Calcula `Get-FileHash -Algorithm SHA256` de ambos. No hay firma de código en Windows: SmartScreen avisará ("Más información → Ejecutar de todas formas").
6. **Riesgo crítico a decidir conmigo**: `model_manager.get_model_path()` guarda el modelo Whisper junto al ejecutable. Un MSI por máquina instala en `Program Files` (sin permiso de escritura para un usuario normal) y la descarga del modelo fallaría. Compruébalo instalando el MSI y el NSIS (el NSIS por usuario va a `%LOCALAPPDATA%\Programs`). Si falla, propón el cambio mínimo (p. ej. `%LOCALAPPDATA%\Markify\models`) y espera mi OK antes de tocar código.
7. **Checklist manual en Windows (la haré yo; tú me la das numerada y corta)**: instalar en VM/equipo limpio; abrir; convertir PNG/JPG ES y EN SIN red (desactivo yo el adaptador, tú no toques ajustes del sistema); PDF de texto, escaneado, mixto, cifrado, ruta con acentos/espacios; DOCX/PPTX con imágenes; `.doc` rechazado al arrastrar; audio (descarga de Whisper, FFmpeg instalado) y vídeo; cancelación; tema; idioma; icono de avisos; desinstalación. Registra resultados contra 2.14b, 3.11b, 4.8b, 7.3b.
8. **Cierre documental**: marca en ambos `tasks.md` las tareas con lo medido; `1.7c` (go/no-go) con una conclusión clara; actualiza `release-notes/v1.1.0-beta.md` (fila de Windows con nombres y SHA-256 de los instaladores, pasos de SmartScreen, quita "not in this release yet"), la sección Download del README y CONTRIBUTING si cambia algo.
9. **Commit/merge**: commits en `develop`; con mi confirmación, push de `develop` y `git merge --ff-only develop` en `main` + push. Sin tags.

## Entregable final
- Los dos instaladores en `%USERPROFILE%\Downloads\` con sus SHA-256.
- Texto final de la descripción del release `v1.1.0-beta` (inglés, mismo estilo que `release-notes/v1.1.0-beta.md`) con la tabla de descargas completa (macOS .dmg + Windows .msi/.exe).
- Pasos exactos en GitHub (web, `gh` no está instalado) para: editar el release `v1.1.0-beta`, adjuntar `.msi` y `.exe`, pegar la nueva descripción, DESMARCAR "pre-release" y marcar "Set as the latest release".
- Resumen de ≤ 150 palabras: qué se hizo y midió, qué NO se pudo verificar, y la siguiente decisión que me toca (incluido archivar los dos changes de OpenSpec).
```
