# check-types

Verifica la consistencia de TypeScript en todo el proyecto Markify.

## Uso
```
/check-types
```

## Pasos

1. **Compilación TypeScript**
```bash
npx tsc --noEmit
```
Corregir TODOS los errores antes de continuar.

2. **Verificar imports de tipos**
   - Todos los tipos deben venir de `src/types/index.ts`
   - No debe haber tipos definidos inline en componentes (excepto props locales simples)
   - `FileStatus`, `AppState`, `ConversionFile`, `Language` — todos en `src/types/index.ts`

3. **Verificar eventos Tauri**
   - Los wrappers `tauriCommands` y `tauriEvents` deben estar en `src/types/index.ts`
   - Los payloads de eventos deben tener tipos explícitos

4. **Verificar stores**
   - Cada store debe exportar su tipo de estado: `AppStore`, `ConversionStore`, `PreviewStore`
   - No usar `any` en ningún store

5. **Reporte final**
Listar cualquier uso de `any`, `unknown` sin narrowing, o assertions (`as`) que puedan ser problemáticas.
