## Context

Markify es un proyecto greenfield de Tauri v2 + React 18 + TypeScript. La spec `01-types.md` define la tipificación completa del frontend: tipos, enums, interfaces, constantes y utilidades. Actualmente no existe `src/types/` ni `src/lib/` (salvo `src/lib/utils.ts` con el helper `cn`). Este cambio es el paso 1 del orden de implementación recomendado y es prerequisito de todos los demás módulos.

**Constraints:**
- Todos los tipos deben vivir en `src/types/index.ts` como fuente única de verdad
- Nunca redefinir tipos localmente en componentes
- El sidecar Python se comunica solo por JSON newline-delimited — no hay API HTTP/REST
- Usar `import type { ... } from '@/types'` en el resto del proyecto

## Goals / Non-Goals

**Goals:**
- Crear todos los type aliases, interfaces y enums definidos en la spec 01
- Crear todas las constantes de extensión, límites y configuración
- Crear funciones utilitarias de archivos (`fileUtils.ts`) y formateo (`formatters.ts`)
- Crear wrappers tipados para comandos Tauri (`invoke`) y eventos (`listen`)
- Exportar todo desde `src/types/index.ts` y `src/lib/` para consumo del resto del proyecto

**Non-Goals:**
- Implementar stores, componentes o lógica de conversión (especs 03, 06, 07, 09)
- Configurar i18n o CSS design system (especs 02, 08)
- Tocar código Rust o Python sidecar
- Crear tests (el spec 01 no los define)

## Decisions

1. **Archivo único `src/types/index.ts` como source of truth**: La spec lo establece explícitamente. Evita duplicación de tipos y facilita refactors. Alternativa rechazada: tipos colocalizados con componentes (viola la spec).

2. **Separación de utilidades por dominio**: `fileUtils.ts` para extensión/categoría, `formatters.ts` para formateo, `tauri.ts` para wrappers Tauri. Aunque podrían caber en un solo archivo, mantenerlos separados alinea con lo definido en la spec y facilita encontrar el código por responsabilidad.

3. **`as const` en arrays de extensiones**: Permite derivar tipos union (`DocumentExtension`, `AudioExtension`, `SupportedExtension`) de las constantes. Elimina duplicación. Si se añade una extensión nueva, basta con modificar el array.

4. **Wrappers tipados de Tauri en lugar de `invoke`/`listen` directo**: El spec 01 define wrappers con tipos explícitos para cada comando y evento. Esto da autocompletado y seguridad de tipos en todo el frontend. Alternativa: usar `invoke` genérico con casting manual (más frágil).

5. **`generateZipName()` incluye fecha con `replace(':', '-')`**: En Windows los dos puntos no son válidos en nombres de archivo. La spec usa este formato desde el diseño.

6. **`formatFileSize()` con división binaria (1024)**: La spec usa `Math.log/1024`. Esto es consistente con cómo los sistemas operativos reportan tamaños de archivo.

## Risks / Trade-offs

- **[Bajo] El archivo `src/types/index.ts` puede crecer con el tiempo**: Mitigación — organizar con comentarios de sección (emojis) como en la spec. Si supera ~300 líneas en el futuro, considerar split por dominio manteniendo barrel export.
- **[N/A] Cambio sin migración**: Al ser greenfield, no hay riesgo de breaking changes.
- **[Bajo] Dependencia de `@tauri-apps/api` en `src/lib/tauri.ts`**: Si el alias `@/` no está configurado en Vite/tsconfig, la importación fallará. Verificar que `tsconfig.json` tenga `paths: { "@/*": ["./src/*"] }`.
