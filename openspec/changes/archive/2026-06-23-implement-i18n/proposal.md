## Why

Los 23 componentes usan textos hardcodeados en español. La spec 08 define la arquitectura i18n con react-i18next + JSONs ES/EN completos. Sin i18n, la app no soporta inglés y los textos no son mantenibles. Es el paso 8 del orden de implementación.

## What Changes

- Crear `src/i18n/index.ts` — configuración de i18next con detector de idioma, namespaces `common` y `messages`
- Crear `src/i18n/locales/es/common.json` — 107 claves de UI en español
- Crear `src/i18n/locales/en/common.json` — 107 claves de UI en inglés
- Crear `src/i18n/locales/es/messages.json` — mensajes de error del sidecar en español
- Crear `src/i18n/locales/en/messages.json` — mensajes de error del sidecar en inglés
- Importar `./i18n/index` en `src/main.tsx` antes del render

## Capabilities

### New Capabilities

- `i18n-config`: Configuración de i18next con LanguageDetector, namespaces, pluralización CLDR
- `i18n-locales`: JSONs de traducción ES/EN para common (UI) y messages (errores)

### Modified Capabilities

N/A.

## Impact

- **Crea:** 5 archivos en `src/i18n/` + modifica `src/main.tsx`
- **Dependencias:** `react-i18next`, `i18next-browser-languagedetector` (npm)
- **Usado por:** todos los componentes que contienen texto visible
