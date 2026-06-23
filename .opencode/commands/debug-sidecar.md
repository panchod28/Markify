# debug-sidecar

Sesión de debug estructurada para problemas con el Python sidecar de Markify.

## Uso
```
/debug-sidecar <descripción del problema>
```
Ejemplo: `/debug-sidecar el sidecar no responde después de enviar el primer archivo`

## Diagnóstico paso a paso

### 1. Verificar que el sidecar arranca
```bash
cd sidecar
echo '{"command":"ping"}' | python main.py
# Debe responder: {"type":"pong"}
```

### 2. Verificar protocolo JSON
- Toda salida a stdout DEBE ser JSON válido, una línea por mensaje
- NUNCA debe haber texto plano en stdout (ni print(), ni traceback sin capturar)
- Los errores de Python van a stderr, no stdout

### 3. Verificar comunicación Tauri → Python
- Revisar `src-tauri/src/lib.rs` función `spawn_sidecar()`
- El sidecar se lanza con `tauri_plugin_shell::process::CommandChild`
- Los mensajes van por `child.stdin` como bytes UTF-8 + `\n`

### 4. Checklist de causas comunes
- [ ] ¿El binario del sidecar existe en `src-tauri/binaries/`?
- [ ] ¿El nombre del binario coincide con `tauri.conf.json → bundle.externalBin`?
- [ ] ¿Python está capturando todas las excepciones antes de que lleguen a stdout?
- [ ] ¿Se está haciendo `sys.stdout.flush()` después de cada write_message()?
- [ ] ¿El `cancel_flag` está siendo chequeado correctamente en whisper_handler?

### 5. Logs útiles
```bash
# Ver stderr del sidecar (errores Python)
# En desarrollo, Tauri muestra stderr en la consola

# Test manual de conversión
echo '{"command":"convert","files":[{"id":"test","path":"/ruta/archivo.pdf","lang":"es"}]}' | python sidecar/main.py
```

## Reglas del protocolo
- `read_message()` en `protocol.py` lee una línea de stdin y hace `json.loads()`
- `write_message()` hace `json.dumps()` + `\n` + `flush()`
- Si stdin se cierra (EOF), el sidecar debe terminar limpiamente
