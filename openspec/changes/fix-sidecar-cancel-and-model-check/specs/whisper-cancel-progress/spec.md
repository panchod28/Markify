## ADDED Requirements

### Requirement: Transcripción cancelable entre ventanas
La transcripción SHALL comprobar el flag de cancelación al terminar cada ventana procesada por Whisper y, si está activo, abortar sin devolver texto parcial como resultado.

#### Scenario: Cancelar un audio largo
- **WHEN** el usuario cancela mientras se transcribe un audio de 113 s
- **THEN** la transcripción se interrumpe al terminar la ventana en curso (segundos, no minutos), se emite `conversion_cancelled` y no se emite `file_result` completado para ese archivo

#### Scenario: Sin cancelación
- **WHEN** el flag no se activa
- **THEN** la transcripción termina con el mismo texto y formato Markdown que antes de este change

### Requirement: Progreso real de transcripción
Mientras transcribe, el sidecar SHALL emitir `file_progress` con `progress` entero creciente entre 0 y 99 según las ventanas procesadas, solo cuando el valor entero cambie. El 100 % SHALL indicarlo únicamente el `file_result`.

#### Scenario: Audio de varias ventanas
- **WHEN** se transcribe un audio de 4 ventanas
- **THEN** se observan valores de progreso crecientes (p. ej. 25, 50, 75) antes del `file_result` con `progress=100`

#### Scenario: Audio de una sola ventana
- **WHEN** se transcribe un audio de menos de 30 s
- **THEN** no se emite más de un valor intermedio y el `file_result` llega con `progress=100`

### Requirement: Restauración y aislamiento del enganche
El enganche en la barra de progreso de Whisper SHALL aplicarse solo durante la llamada a `transcribe` y SHALL restaurarse siempre (también ante excepciones o cancelación).

#### Scenario: Excepción durante la transcripción
- **WHEN** `transcribe` lanza una excepción inesperada
- **THEN** `whisper.transcribe.tqdm` queda restaurado al original y el error se propaga con el mensaje existente

### Requirement: Degradación si cambia la API interna
Si el punto de enganche de Whisper no existe en la versión instalada, el sidecar SHALL registrar un aviso en stderr y transcribir como antes (sin cancelación intermedia ni progreso real), sin fallar.

#### Scenario: Versión incompatible de Whisper
- **WHEN** `whisper.transcribe` no expone `tqdm`
- **THEN** la transcripción se completa correctamente y se registra `[Sidecar] whisper hook no disponible` en stderr

### Requirement: Versión de Whisper acotada y vigilada
`requirements.txt` SHALL fijar la versión de `openai-whisper` probada y una prueba automatizada SHALL fallar si el punto de enganche deja de existir en el entorno de prueba.

#### Scenario: Actualización de dependencias
- **WHEN** se instala una versión de Whisper sin `whisper.transcribe.tqdm`
- **THEN** la prueba de enganche falla en CI antes de publicar

### Requirement: Stdout solo con mensajes del protocolo durante la transcripción
Mientras transcribe, el sidecar SHALL NOT escribir en stdout nada que no sea un mensaje JSON del protocolo (por ejemplo, el aviso de idioma detectado de Whisper).

#### Scenario: Transcripción de un audio en español
- **WHEN** se transcribe un audio y se captura stdout
- **THEN** todas las líneas son JSON válido y no aparece `Detected language`
