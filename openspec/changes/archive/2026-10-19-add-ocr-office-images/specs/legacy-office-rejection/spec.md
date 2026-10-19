## ADDED Requirements

### Requirement: Rechazo claro de `.doc` y `.ppt` en la interfaz
La aplicación SHALL dejar de ofrecer `.doc` y `.ppt` entre los formatos soportados y SHALL rechazar su selección o arrastre con un mensaje que indique el formato antiguo y qué hacer ("guárdalo como .docx/.pptx"), en español e inglés, sin afectar al resto de los archivos del lote.

#### Scenario: Arrastrar un `.doc` junto a un `.docx`
- **WHEN** el usuario arrastra `informe.doc` e `informe.docx`
- **THEN** se añade `informe.docx`, y un aviso indica que `.doc` es un formato antiguo y debe guardarse como `.docx`

#### Scenario: Selector de archivos
- **WHEN** el usuario abre el selector de archivos
- **THEN** `.doc` y `.ppt` no figuran entre las extensiones ofrecidas

### Requirement: Distinción respecto a formatos no soportados
El rechazo de `.doc` y `.ppt` SHALL usar un tipo de error de validación propio (`legacy_format`), distinto del de extensión no soportada, para poder mostrar el mensaje específico. `.xls` SHALL seguir aceptándose.

#### Scenario: Extensión desconocida
- **WHEN** el usuario arrastra un `.xyz`
- **THEN** se muestra el mensaje genérico de formato no soportado y no el de formato antiguo

#### Scenario: Excel antiguo
- **WHEN** el usuario arrastra un `.xls`
- **THEN** el archivo se añade y se convierte como hasta ahora

### Requirement: Defensa en el sidecar
Si un archivo `.doc` o `.ppt` llegara al sidecar, el sistema SHALL fallar con `ConversionError(code="legacy_format")` y el mismo mensaje localizado, en lugar del error genérico.

#### Scenario: `.ppt` que llega al sidecar
- **WHEN** `handle_convert` recibe un archivo con extensión `.ppt`
- **THEN** el archivo termina con error y el mensaje "Formato antiguo: guárdalo como .pptx" y el lote continúa
