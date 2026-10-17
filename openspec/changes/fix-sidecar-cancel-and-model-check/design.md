## Context

**Evidencia** (build `--onedir`, macOS, UI real):
- `check_model` desde la UI: el sidecar sí responde `{"type":"model_status","payload":{"available":true}}` (verificado por stdin), pero `handle_sidecar_output` en Rust solo completa la comprobación si `msg["request_id"]` existe (`src-tauri/src/commands/sidecar.rs`). Sin ese campo la petición expira (hoy 60 s) y el frontend conserva `false`.
- `main()` es un único bucle: `read_message()` → `handle_convert()` (bloqueante) → siguiente `read_message()`. Un `cancel` escrito mientras se convierte queda en el pipe hasta que termina la conversión; entonces `_cancel_flag.set()` ya no sirve para nada (el siguiente `convert` hace `clear()`).
- `whisper_handler.transcribe_audio` llama a `model.transcribe()` (una sola llamada larga) y solo mira `cancel_flag` antes y después; el progreso emitido es 0 % → 50 % → 100 %.
- `openai-whisper` 20250625 envuelve el bucle por ventanas de 30 s en `with tqdm.tqdm(total=content_frames, unit="frames", disable=verbose is not False) as pbar:` y llama a `pbar.update(avance)` en cada ventana (`whisper/transcribe.py`).
- `store.resetToEmpty` hace `set(INITIAL_CONVERSION_STATE)`, que incluye `whisperModelAvailable: false`.
- Efecto en pantalla: modal de descarga siempre que hay audio; descarga repetida de 145 MB; cancelación que termina en "convertido correctamente".

## Goals / Non-Goals

**Goals**
- `check_model` responde correctamente y en cualquier momento (incluso durante una conversión).
- `cancel` actúa en segundos: entre archivos, entre ventanas de Whisper y (futuro OCR) entre páginas.
- Progreso real de audio.
- Sin cambios de protocolo hacia Rust/frontend más allá de `request_id` y un `progress` más fino.

**Non-Goals**
- Cancelar la descarga del modelo, descargar a un `.part` y renombrar (hoy un `base.pt` truncado > 100 MB cuenta como "existe"), mover el modelo fuera del `.app`.
- Paralelizar conversiones (sigue habiendo un único trabajador).
- Interrumpir una ventana de Whisper a mitad de cálculo, la carga del modelo o la decodificación inicial con ffmpeg (latencia de cancelación = lo que tarde una ventana).
- Arreglar `check_model` por otros medios en Rust (el contrato `request_id` ya existe; se corrige el emisor).

## Decisions

### D1. Lector + trabajador con `queue.Queue` (no asyncio)

Un hilo daemon lee stdin y despacha:

| Comando | Quién lo atiende | Por qué |
|---|---|---|
| `cancel` | lector, al instante: `_cancel_flag.set()` | debe actuar mientras el trabajador está ocupado |
| `check_model` | lector, al instante: responde `model_status` con `request_id` | es barato y no debe esperar a una conversión larga |
| `convert`, `download_model` | cola FIFO → trabajador (hilo principal) | trabajo largo y secuencial, igual que hoy |
| EOF | lector encola un centinela y termina | el trabajador sale y el proceso termina como hoy |

*Alternativa descartada — `asyncio`*: reescritura del sidecar para un problema que resuelve un hilo y una cola. *Alternativa descartada — hilo por conversión*: permite solapar trabajos y exige proteger MarkItDown/Whisper sin necesidad.

### D2. Semántica del flag de cancelación sin carreras

El **lector** hace `_cancel_flag.clear()` justo al **encolar** cada `convert` (no el trabajador al empezarlo). Así un `cancel` que llegue después de ese `convert`, aunque el trabajador aún no lo haya sacado de la cola, se conserva y el primer chequeo del bucle lo respeta. Un `cancel` sin conversión activa deja el flag activo hasta el siguiente `convert`, que lo limpia al encolarse: no hay cancelaciones "fantasma". `cancel` durante `download_model` no se aplica a la descarga (non-goal) y se descarta de la misma forma.

### D3. `dispatcher.py`: despacho puro y testeable

`main.py` importa torch/whisper al cargarse, lo que impide testear el bucle. El despacho (lector, cola, flag, reglas de D1–D2) pasa a `dispatcher.py` con **handlers inyectados** (`handle_convert`, `handle_download_model`, `model_status`) y sin imports pesados. `main.py` solo conecta los handlers reales. Cumple "responsabilidad única" y permite pruebas con handlers falsos. No se introduce ninguna abstracción más.

### D4. Escritura segura entre hilos

`protocol.write_message` toma un `threading.Lock` módulo-global alrededor de `write` + `flush`: dos hilos (lector respondiendo `check_model`, trabajador emitiendo progreso) nunca intercalan líneas. El resto de la regla ("solo JSON, `flush` siempre, nada de `print`") no cambia.

### D5. `request_id`

`model_status` incluye `"request_id": msg.get("id")` (el `id` que Rust ya envía en `check_model`). Rust ya lo consume; no se toca. Si `id` falta, el campo es `null` (comportamiento actual).

### D6. Cancelación y progreso de Whisper vía el hook de `tqdm`

Dentro de `transcribe_audio`, mientras dura `model.transcribe(...)`, se sustituye `whisper.transcribe.tqdm` por un objeto con una clase `tqdm` mínima (context manager con `update(n)`): en cada `update` (una por ventana de ~30 s) comprueba `cancel_flag`; si está activo lanza `TranscriptionCancelled` (excepción propia, capturada en `transcribe_audio`, que devuelve `""` como hoy, de modo que `main`/`handle_convert` no cambian su lógica de `conversion_cancelled`); si no, emite `file_progress` con `progress = min(99, int(100*hecho/total))` solo cuando el entero cambia (el 100 lo marca el `file_result`). El parche se restaura en `finally`.

**Stdout limpio**: la llamada actual usa `verbose=False`, con lo que Whisper imprime `Detected language: Spanish` en **stdout** (verificado en el sidecar compilado): una línea que no es JSON y que Rust descarta con un log. Con `verbose=None` Whisper no imprime nada y, como el shim reemplaza a `tqdm`, el progreso funciona igual. No se usa `contextlib.redirect_stdout` porque cambiaría `sys.stdout` para todos los hilos y desviaría a stderr las respuestas que escribe el lector.

*Alternativa descartada — trocear el audio en ventanas propias y llamar a `transcribe` por trozo*: corta palabras en los bordes y pierde el contexto entre ventanas (peor calidad). *Alternativa descartada — matar/aislar la transcripción en otro proceso*: complejidad y memoria dobles. *Alternativa descartada — dejarlo como está*: cancelar no funciona.

**Degradación**: si `whisper.transcribe` ya no expone `tqdm` (otra versión), se registra un aviso en stderr y se transcribe como hoy (sin cancelación intermedia ni progreso real). Se **acota la versión** de `openai-whisper` en `requirements.txt` a la probada (20250625) y una prueba unitaria falla si cambia el punto de enganche.

### D7. Frontend

`resetToEmpty` conserva los campos `whisperModel*` (`set({...INITIAL_CONVERSION_STATE, whisperModelAvailable: get().whisperModelAvailable, …})`). El resto del flujo (`checkWhisperModel` al montar, `try/catch` ya añadido por `sidecar-onedir`, modal solo si `hasAudio && !available`) no cambia. Con D5 la comprobación inicial resolverá `true` cuando el modelo exista.

### D8. Errores y trazabilidad

El lector nunca debe morir: cada comando se despacha dentro de `try/except` que registra en stderr (`[Sidecar] …` + traceback, como hoy) y sigue leyendo. JSON inválido o comando desconocido se registran y se ignoran (comportamiento actual). Un fallo en el trabajador sobre un archivo sigue produciendo `file_result` con error (sin cambios).

## Estrategia de pruebas

- **Unitarias (sin torch)**, `sidecar/tests/test_dispatcher.py` con handlers falsos: (1) `cancel` se procesa mientras un `convert` falso está bloqueado (Event) y el handler lo ve; (2) `check_model` responde con `request_id` mientras el trabajador está ocupado; (3) `convert` + `cancel` inmediato → el handler ve el flag activo; (4) `cancel` ocioso + `convert` posterior → flag limpio; (5) EOF termina el trabajador tras vaciar la cola; (6) una excepción en un handler no mata al lector.
- **Concurrencia de salida**, `test_protocol.py`: 8 hilos × 200 mensajes → todas las líneas son JSON válido y completas.
- **Shim de progreso**, `test_whisper_progress.py` (sin modelo): `update` con flag inactivo emite progreso monótono y acotado a 99; con flag activo lanza `TranscriptionCancelled`; el context manager restaura `whisper.transcribe.tqdm`; comprueba que `whisper.transcribe.tqdm` existe (alarma si cambia la versión).
- **Smoke** (`smoke_test.py`): `check_model` con `id` devuelve `request_id` idéntico.
- **Manual en macOS con la app real** (computer-use o a mano): audio largo → Cancelar → "Cancelando…" resuelve en segundos y la lista vuelve a "archivos listos"; audio corto → completa con progreso creciente; con el modelo ya descargado, añadir un audio **no** muestra el modal, ni tras "Nueva conversión".

## Risks / Trade-offs

- **[Dependencia de internals de Whisper]** → versión acotada + prueba de alarma + degradación documentada (D6).
- **[Cancelación no instantánea]** → latencia = una ventana de Whisper (varios segundos en CPU); se documenta y la UI ya muestra "Cancelando…".
- **[Concurrencia introduce condiciones de carrera]** → el diseño minimiza superficie (un trabajador, dos comandos atendidos en el lector, lock en la salida, flag con `Event`) y las pruebas D1–D2 cubren los casos de orden.
- **[Cancelación durante `download_model`]** → no soportada; se descarta sin efectos (D2).
- **[Modelo truncado cuenta como existente]** → fuera de alcance, anotado.

## Migration Plan

Cambio interno al sidecar y una línea del store; no hay migración de datos. Despliegue en una sola entrega (el `request_id` extra es ignorado por versiones antiguas de Rust). Rollback: revertir el commit; el comportamiento vuelve al actual.

## Open Questions

1. ¿Acotar `openai-whisper` a `==20250625` (más seguro) o a `>=20250625,<2027` (menos fricción)? Por defecto **`==20250625`**.
2. ¿Aceptas que cancelar espere hasta el final de la ventana de Whisper en curso? Por defecto **sí** (alternativas descartadas en D6).
3. ¿Quieres además que `download_model` descargue a `base.pt.part` y renombre al terminar (evita el modelo truncado)? Por defecto **no**, change aparte.
