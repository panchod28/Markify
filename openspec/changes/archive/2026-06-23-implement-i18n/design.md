## Context

El spec 08-i18n.md define la arquitectura i18n completa con react-i18next. Ya existen los componentes con texto hardcodeado. Este cambio crea la infraestructura i18n que los componentes usarán via `useTranslation()`.

## Goals / Non-Goals

**Goals:**
- Configurar i18next con detector de idioma y 2 namespaces
- Crear JSONs ES/EN con todas las claves de UI y errores
- Importar i18n en main.tsx

**Non-Goals:**
- Actualizar componentes para usar `useTranslation()` (se hará incrementalmente)

## Decisions

1. **`load: 'languageOnly'`**: Mapea `es-MX` → `es`, `en-US` → `en`. Solo 2 archivos de traducción.

2. **Recursos embebidos, no lazy-loading**: La app es offline y los JSONs son pequeños (~3 KB cada uno). Cargarlos todos al inicio.

3. **Pluralización CLDR con `_one`/`_other`**: Español e inglés usan solo estas dos formas. Suficiente para todos los casos de la app.

4. **Namespace `messages` separado de `common`**: Los errores del sidecar son técnicamente generados por Python, pero se referencian en la UI. Namespace separado mantiene organización.
