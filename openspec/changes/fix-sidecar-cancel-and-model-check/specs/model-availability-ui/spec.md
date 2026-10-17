## ADDED Requirements

### Requirement: Comprobación del modelo al abrir
Al montar la app, el frontend SHALL consultar la disponibilidad del modelo Whisper y SHALL reflejar el resultado real en `whisperModelAvailable`, incluso cuando el sidecar tarda en el primer arranque.

#### Scenario: Modelo ya descargado
- **WHEN** el modelo existe en disco y se abre la app
- **THEN** `whisperModelAvailable` pasa a `true` sin intervención del usuario

#### Scenario: Modelo ausente
- **WHEN** el modelo no existe
- **THEN** `whisperModelAvailable` es `false` y el modal de descarga aparece solo al convertir un audio

### Requirement: El modal solo aparece si falta el modelo
El modal de descarga SHALL mostrarse únicamente si hay archivos de audio, el modelo no está disponible y el usuario no lo ha descartado.

#### Scenario: Audio con el modelo disponible
- **WHEN** el modelo está disponible y el usuario pulsa Convertir con un audio
- **THEN** la conversión empieza sin mostrar el modal ni descargar nada

### Requirement: Disponibilidad conservada entre conversiones
`resetToEmpty` (Nueva conversión) SHALL conservar `whisperModelAvailable` y el resto del estado del modelo Whisper.

#### Scenario: Segunda conversión de audio
- **WHEN** el modelo se descargó o ya existía, el usuario termina una conversión, pulsa Nueva conversión y añade otro audio
- **THEN** al convertir no se muestra el modal de descarga

### Requirement: Fallo de comprobación sin efectos
Si la comprobación falla o expira, el estado previo SHALL conservarse y el error SHALL registrarse en consola, sin romper la app.

#### Scenario: Sidecar sin respuesta
- **WHEN** el sidecar no responde a `check_model`
- **THEN** la app sigue usable y `whisperModelAvailable` conserva su valor anterior
