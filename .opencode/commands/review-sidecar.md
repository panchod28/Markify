# review-sidecar

Revisa el código del Python sidecar antes de hacer commit o build.

## Uso
```
/review-sidecar
```

## Checklist de revisión

### protocol.py
- [ ] `read_message()` maneja `EOFError` y termina el proceso limpiamente
- [ ] `write_message()` siempre llama `sys.stdout.flush()`
- [ ] No hay ningún `print()` que escriba a stdout

### main.py
- [ ] El loop principal captura todas las excepciones
- [ ] Cada comando desconocido responde con `{"type":"error","message":"unknown command"}`
- [ ] El `cancel_flag` es un `threading.Event()` compartido correctamente
- [ ] `handle_convert()` verifica `cancel_flag.is_set()` entre archivos

### converter.py
- [ ] `MarkItDown()` se instancia una sola vez (no por archivo)
- [ ] Todos los errores de conversión están mapeados en `error_messages.py`
- [ ] El resultado incluye: `{"type":"file_complete","id":"...","markdown":"..."}`

### whisper_handler.py
- [ ] Verifica `cancel_flag.is_set()` antes de cargar el modelo
- [ ] Verifica `cancel_flag.is_set()` antes de transcribir
- [ ] El output markdown incluye el header con nombre de archivo y duración

### model_manager.py
- [ ] `model_exists()` verifica tamaño > 100MB (no solo existencia del archivo)
- [ ] `download_model()` reporta progreso via `write_message({"type":"model_progress",...})`
- [ ] La descarga usa `urllib.request` con reporthook para el progreso

### Verificación final
```bash
cd sidecar
python -m py_compile main.py protocol.py converter.py whisper_handler.py model_manager.py error_messages.py
echo "Sin errores de sintaxis ✓"
```
