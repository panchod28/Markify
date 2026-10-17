> Cambio acotado al sidecar y a una línea del store. Rust no cambia.

## 1. Despacho y `check_model` (corrige el modal permanente)

- [x] 1.1 `protocol.write_message`: `threading.Lock` alrededor de `write` + `flush`; test de 8 hilos × 200 mensajes
- [x] 1.2 Crear `sidecar/dispatcher.py`: hilo lector, `queue.Queue`, atención inmediata de `cancel` y `check_model`, encolado de `convert`/`download_model`, `clear()` del flag al encolar `convert`, centinela en EOF, `try/except` por comando con log a stderr
- [x] 1.3 `main.py`: conectar handlers reales al dispatcher (el trabajador es el hilo principal); `model_status` con `request_id`; sin cambios en `handle_convert` salvo lo imprescindible
- [x] 1.4 `tests/test_dispatcher.py` con handlers falsos: cancel durante convert, check_model durante convert, convert+cancel inmediato, cancel ocioso, EOF, handler que lanza excepción
- [x] 1.5 `smoke_test.py`: enviar `check_model` con `id` y verificar `request_id`
- [x] 1.6 Verificado en macOS (sidecar compilado, modelo `base`, audio de 113 s): `check_model` durante la transcripción responde en 0.00 s con `request_id` y `available=true`

## 2. Whisper cancelable con progreso real

- [x] 2.1 `whisper_handler.py`: llamar a `transcribe(..., verbose=None)` (con `verbose=False` Whisper imprime "Detected language: …" en **stdout**, línea que no es JSON y viola el protocolo; no redirigir `sys.stdout` porque el lector escribe a la vez) y shim `tqdm` (context manager con `update`) que consulta `cancel_flag`, lanza `TranscriptionCancelled` y emite `file_progress` (0–99, solo si cambia el entero); aplicar y restaurar en `try/finally` alrededor de `model.transcribe`
- [x] 2.2 Captura de `TranscriptionCancelled` en `transcribe_audio` → devuelve `""`; confirmar que `handle_convert` emite `conversion_cancelled` y no `file_result`
- [x] 2.3 Degradación: sin `whisper.transcribe.tqdm` → aviso en stderr y comportamiento previo
- [x] 2.4 `requirements.txt`: fijar `openai-whisper==20250625` (ver Open Question 1)
- [x] 2.5 `tests/test_whisper_progress.py`: progreso monótono ≤ 99, sin texto no-JSON en stdout, cancelación, restauración del atributo, existencia de `whisper.transcribe.tqdm`
- [x] 2.6 Verificado en macOS (sidecar compilado, modelo `base`, audio de 113 s): sin cancelar, progreso 0 → 25 → 46 y `file_result` en 33 s; cancelando a los 12 s, `conversion_cancelled` 8.5 s después (una ventana de Whisper) y sin `file_result`; ninguna línea no-JSON en stdout

## 3. Frontend

- [ ] 3.1 `useConversionStore.resetToEmpty`: conservar `whisperModelAvailable` y los campos `whisperModel*`
- [ ] 3.2 Test vitest del store: `resetToEmpty` no reinicia la disponibilidad (el repo aún no tiene tests de vitest: crear solo lo mínimo)
- [ ] 3.3 `npm run type-check` y `npm run test` sin errores

## 4. Verificación de extremo a extremo (macOS)

- [ ] 4.1 Build `--onedir` + app: con el modelo ya descargado, abrir la app, añadir audio y pulsar Convertir → **sin** modal; tras "Nueva conversión" tampoco
- [ ] 4.2 Audio largo → Cancelar → la UI sale de "Cancelando…" en segundos y vuelve a archivos listos; sin `file_result` completado
- [ ] 4.3 Lote mixto (DOCX + audio + CSV) cancelado a mitad: los archivos no procesados no se ejecutan
- [ ] 4.4 Cierre de la app durante una transcripción: el sidecar termina (sin procesos huérfanos)
- [ ] 4.5 Repetir 4.1–4.4 en Windows (VM o CI)

## 5. CI

- [ ] 5.1 El job de tests del sidecar ejecuta `pytest` (dispatcher, protocolo, shim) en macOS y Windows
- [ ] 5.2 Confirmar que el smoke test de `sidecar-onedir` sigue pasando con el nuevo bucle

## 6. Docs y cierre

- [ ] 6.1 Actualizar spec `05-sidecar-protocol` (hilos, `request_id`, semántica del flag, progreso de audio) y `03-stores` (`resetToEmpty`)
- [ ] 6.2 Nota en CONTRIBUTING: el hook de Whisper depende de `whisper.transcribe.tqdm` y qué hacer al actualizar
- [ ] 6.3 `openspec validate fix-sidecar-cancel-and-model-check --strict` y archivar
