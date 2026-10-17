## ADDED Requirements

### Requirement: Lectura de comandos desacoplada de la ejecución
El sidecar SHALL leer stdin en un hilo propio mientras un único trabajador ejecuta `convert` y `download_model` en orden de llegada. El hilo lector SHALL NOT quedar bloqueado por un trabajo en curso.

#### Scenario: Comando recibido durante una conversión
- **WHEN** el trabajador está procesando un archivo y llega `check_model` por stdin
- **THEN** el sidecar responde `model_status` sin esperar a que termine la conversión

#### Scenario: Orden de trabajos
- **WHEN** llegan dos comandos `convert` seguidos
- **THEN** se ejecutan uno después de otro, en el orden recibido

### Requirement: Cancelación inmediata del flag
Al recibir `cancel`, el sidecar SHALL activar el flag de cancelación de inmediato, sin esperar al trabajador, de modo que el trabajo en curso lo observe en su siguiente punto de control.

#### Scenario: Cancelar a mitad de un lote
- **WHEN** el trabajador procesa el archivo 2 de 5 y llega `cancel`
- **THEN** el flag queda activo de inmediato y, al terminar o interrumpirse el archivo actual, se emite `conversion_cancelled` sin procesar los archivos 3 a 5

### Requirement: Flag sin carreras ni cancelaciones fantasma
El flag SHALL limpiarse al encolar cada `convert` (no al empezar a ejecutarlo). Un `cancel` posterior a ese encolado SHALL conservarse aunque el trabajador aún no haya iniciado el `convert`. Un `cancel` recibido sin conversión activa ni encolada SHALL NOT afectar a una conversión posterior.

#### Scenario: Cancelar antes de que empiece el trabajo
- **WHEN** llegan `convert` y, de inmediato, `cancel`, antes de que el trabajador saque el `convert` de la cola
- **THEN** el trabajador observa el flag activo y emite `conversion_cancelled` sin procesar archivos

#### Scenario: Cancelación ociosa
- **WHEN** llega `cancel` sin ninguna conversión en curso y después llega un `convert` nuevo
- **THEN** la nueva conversión se ejecuta completa

### Requirement: Respuesta correlacionada de `check_model`
`model_status` SHALL incluir `request_id` con el valor del `id` recibido en el comando `check_model`.

#### Scenario: Comprobación del modelo existente
- **WHEN** llega `{"id":"abc","command":"check_model"}` y el modelo está en disco
- **THEN** se emite `{"type":"model_status","request_id":"abc","payload":{"available":true}}`

#### Scenario: Comando sin id
- **WHEN** llega `check_model` sin `id`
- **THEN** `request_id` es `null` y el resto del mensaje es el mismo

### Requirement: Escritura de salida segura entre hilos
`write_message` SHALL serializar las escrituras con un lock de modo que cada mensaje JSON aparezca completo en una línea propia, con `flush`, aunque lo invoquen varios hilos a la vez.

#### Scenario: Escritores concurrentes
- **WHEN** 8 hilos escriben 200 mensajes cada uno
- **THEN** las 1 600 líneas de stdout son JSON válidos e íntegros

### Requirement: Resiliencia del lector y apagado limpio
Un error al despachar un comando SHALL registrarse en stderr (sin stdout) y el lector SHALL seguir leyendo. Al cerrarse stdin (EOF) el sidecar SHALL terminar tras completar o descartar la cola de forma ordenada.

#### Scenario: Handler que lanza excepción
- **WHEN** el handler de `check_model` lanza una excepción
- **THEN** se registra el error en stderr y un `cancel` posterior se sigue atendiendo

#### Scenario: Cierre de la app
- **WHEN** Tauri cierra stdin
- **THEN** el proceso del sidecar termina sin quedar huérfano
