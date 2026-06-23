# build-check

Checklist pre-build para distribuir Markify en Mac, Windows o Linux.

## Uso
```
/build-check <plataforma>
```
Ejemplo: `/build-check mac`

## Checklist común (todas las plataformas)

### Frontend
- [ ] `npx tsc --noEmit` — sin errores TypeScript
- [ ] `npm run build` — Vite build sin warnings críticos
- [ ] Todos los textos en ES y EN (revisar `src/i18n/locales/`)
- [ ] Tema claro y oscuro funcionando (probar con `data-theme="dark"` en `<html>`)

### Python sidecar
- [ ] `python -m py_compile sidecar/*.py` — sin errores de sintaxis
- [ ] `cd sidecar && python build.py` — PyInstaller genera el binario
- [ ] Binario copiado a `src-tauri/binaries/` con el nombre correcto:
  - Mac: `markify-sidecar-aarch64-apple-darwin` o `x86_64-apple-darwin`
  - Windows: `markify-sidecar-x86_64-pc-windows-msvc.exe`
  - Linux: `markify-sidecar-x86_64-unknown-linux-gnu`
- [ ] Binario tiene permisos de ejecución (`chmod +x` en Mac/Linux)

### Tauri
- [ ] `tauri.conf.json → bundle.externalBin` incluye la ruta al sidecar
- [ ] Íconos en `src-tauri/icons/` para la plataforma objetivo
- [ ] `productName`, `version` y `identifier` correctos en `tauri.conf.json`

## Build por plataforma

### Mac
```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/dmg/Markify_*.dmg
```

### Windows (desde Windows o cross-compile)
```bash
npm run tauri build -- --target x86_64-pc-windows-msvc
# Output: src-tauri/target/release/bundle/nsis/Markify_*_x64-setup.exe
```

### Linux
```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/deb/markify_*.deb
#         src-tauri/target/release/bundle/appimage/markify_*.AppImage
```

## Notas de distribución (sin code signing)
- **Mac**: usuario hace clic derecho → Abrir → Confiar. Solo la primera vez.
- **Windows**: SmartScreen → "Más información" → "Ejecutar de todas formas". Solo la primera vez.
- **Linux**: Sin restricciones.
