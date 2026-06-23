# propose-feature

Crea una propuesta OpenSpec para una nueva feature o cambio en Markify.

## Uso
```
/propose-feature <descripción>
```
Ejemplo: `/propose-feature agregar soporte para archivos .epub`

## Instrucciones

Este comando sigue el flujo OpenSpec para proponer cambios de forma estructurada.

### Paso 1 — Crear la propuesta
Genera los siguientes archivos en `openspec/changes/<nombre-kebab>/`:

**proposal.md** — ¿Por qué hacemos esto?
```markdown
# Propuesta: <nombre>
## Problema
## Solución propuesta
## Impacto en el usuario
## Archivos afectados
## Fuera de alcance
```

**specs/** — ¿Qué debe hacer exactamente?
- Casos de uso
- Criterios de aceptación
- Edge cases

**design.md** — ¿Cómo lo implementamos técnicamente?
- Cambios en tipos (`01-types.md`)
- Cambios en stores (`03-stores.md`)
- Cambios en componentes (`06-components.md`)
- Cambios en sidecar Python (si aplica)

**tasks.md** — Lista ordenada de tareas de implementación
```markdown
## Tareas
- [ ] 1.1 Descripción tarea
- [ ] 1.2 Descripción tarea
- [ ] 2.1 Descripción tarea
```

### Paso 2 — Revisar con el usuario
Mostrar los archivos creados y esperar aprobación antes de implementar.

### Paso 3 — Implementar
Usar `/implement-spec` o ejecutar las tareas del `tasks.md` en orden.

### Paso 4 — Archivar
Cuando todo esté implementado y probado:
```
/opsx:archive
```
O mover la carpeta a `openspec/changes/archive/`
