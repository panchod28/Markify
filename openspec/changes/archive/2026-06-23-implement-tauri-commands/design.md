## Context

Markify usa Tauri v2 con sidecar Python para el procesamiento de archivos. La comunicación entre React y Rust es via `invoke` (comandos) y `listen` (eventos). Entre Rust y Python es via stdin/stdout con JSON newline-delimited. El spec `04-tauri-commands.md` define 8 comandos, 6 eventos, el spawn del sidecar y la configuración de plugins/permisos.

El backend Rust actual tiene estructura Tauri v2 mínima (generada por `create-tauri-app`). No hay comandos ni sidecar implementados.

## Goals / Non-Goals

**Goals:**
- Implementar 8 comandos Tauri con tipos correctos y manejo de errores
- Implementar spawn del sidecar Python con loop de stdout y traducción a eventos
- Configurar todos los plugins Tauri necesarios (shell, dialog, fs, store)
- Configurar permisos de capabilities y CSP
- Estructurar el código Rust en módulos separados por responsabilidad

**Non-Goals:**
- Implementar el sidecar Python (spec 05)
- Generar el binario del sidecar (spec 10-build)
- Implementar la UI de componentes React
- Manejar múltiples sidecars en paralelo

## Decisions

1. **`Mutex<CommandChild>` para acceso compartido al sidecar**: Varios comandos necesitan escribir al stdin del sidecar. `Mutex` de Tokio permite acceso exclusivo asíncrono. Se registra con `app.manage()` para que esté disponible en todos los comandos.

2. **Loop de stdout en `tauri::async_runtime::spawn`**: El loop de lectura corre en background sin bloquear el thread principal. Cada línea JSON se parsea y se traduce al evento Tauri correspondiente.

3. **Módulos separados (`commands/conversion.rs`, `file_system.rs`, `sidecar.rs`)**: Separa comandos de conversión, operaciones de archivo y gestión del sidecar. `mod.rs` re-exporta todo limpio.

4. **`check_whisper_model` usa `tokio::sync::oneshot`**: Es el único comando que espera respuesta directa del sidecar (los demás retornan inmediato y emiten eventos). Un channel oneshot permite awaitar la respuesta del loop de stdout.

5. **ZIP via crate `zip` 0.6**: Crea ZIP en memoria sin archivos temporales. `Deflated` como compresión estándar. Alternativa: `flate2` (más manual).

6. **`open_in_folder` con `#[cfg]` por plataforma**: macOS usa `open -R`, Windows `explorer /select`, Linux `xdg-open <folder>`. Compilación condicional evita código muerto.

7. **UUID v4 para mensajes al sidecar**: Cada mensaje tiene un `id` único para correlación en logs. La crate `uuid` con feature `v4` lo genera.

8. **CSP restrictivo**: `default-src 'self'` con `style-src 'unsafe-inline'` para Tailwind. Scripts solo de la app.

## Risks / Trade-offs

- **[Medio] `Mutex<CommandChild>` puede causar deadlocks**: Si un comando adquiere el lock y nunca lo libera. Mitigación: las escrituras al sidecar son rápidas (<1ms), siempre usan `await` y nunca hacen blocking IO dentro del lock.
- **[Bajo] `check_whisper_model` con timeout de 5s**: Si el sidecar no responde, el comando falla. Mitigación: el oneshot channel tiene timeout explícito.
- **[Bajo] El sidecar debe existir en `src-tauri/binaries/`**: Si no, el spawn falla silenciosamente. Mitigación: documentar en tasks que el binario se crea en spec 10.
