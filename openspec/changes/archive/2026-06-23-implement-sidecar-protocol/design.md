## Context

El sidecar Python es un proceso hijo lanzado por Tauri vía `tauri-plugin-shell`. Se comunica exclusivamente por stdin/stdout usando JSON newline-delimited. Rust escribe comandos al stdin, Python lee, procesa y responde por stdout. Stderr es solo para logs internos.

El spec `05-sidecar-protocol.md` define el protocolo completo y provee código Python completo para los 7 módulos + requirements.txt. El diseño ya está especificado — este documento solo documenta las decisiones de implementación.

## Goals / Non-Goals

**Goals:**
- Implementar 7 módulos Python que forman el sidecar completo
- Garantizar que stdout solo contiene JSON (nunca print() sin formato)
- Implementar cancelación vía flag thread-safe (`threading.Event`)
- Descargar modelo Whisper con barra de progreso callback
- Mensajes de error localizados ES/EN

**Non-Goals:**
- Empaquetar con PyInstaller (spec 10-build)
- Modificar el código Rust del sidecar management
- Soporte de GPU (siempre CPU via `fp16=False` + `torch+cpu`)

## Decisions

1. **`threading.Event` para cancel_flag**: El loop principal es single-thread pero la cancelación puede llegar desde stdin en cualquier momento. `threading.Event` es thread-safe y no requiere locks explícitos.

2. **MarkItDown singleton**: Se instancia una vez como variable de módulo. Es thread-safe y mantiene estado interno que mejora rendimiento en conversiones repetidas.

3. **Whisper `base` model siempre**: Modelo de 145 MB, buen balance calidad/velocidad. No se permite cambiar en v1.

4. **Modelo en `~/.markify/models/whisper/` en dev, junto al binario en producción**: `sys.frozen` (PyInstaller) determina la ruta. La carpeta se crea automáticamente.

5. **Progreso de transcripción falso (50%)**: Whisper no expone progreso real por segmento de forma accesible. Se emite 0% al empezar, 50% al terminar transcripción, y el resultado final con 100%.

6. **`urllib.request.urlretrieve` para descarga del modelo**: Con `reporthook` para progreso. Más simple que `requests` y sin dependencia extra.

## Risks / Trade-offs

- **[Medio] Errores de `print()` accidental a stdout rompen el protocolo**: Cualquier output no-JSON a stdout es interpretado por Rust y causa errores de parseo. Mitigación: todas las funciones usan `write_message()`, los prints de debug van a `sys.stderr`.
- **[Bajo] El modelo Whisper pesa 145 MB**: La primera ejecución requiere descarga. Mitigación: UI muestra barra de progreso y el modelo persiste en disco.
- **[Bajo] Torch CPU es más lento que GPU**: Para archivos largos (>30 min) la transcripción puede tardar. Mitigación: la UI muestra progreso y permite cancelar.
