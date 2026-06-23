# Spec 09 — File Processing Pipeline & Sanitization
> Markify — Pipeline completo de conversión de archivos y algoritmo de sanitización de nombres.
> Dependencias: spec `01-types.md`, spec `05-sidecar-protocol.md`

---

## 1. Pipeline completo end-to-end

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE CONVERSIÓN COMPLETO                  │
│                                                                     │
│  FASE 1: VALIDACIÓN (Frontend — antes de convertir)                 │
│  ──────────────────────────────────────────────────                 │
│  Input: File[] del drag & drop o file picker                        │
│     ↓                                                               │
│  Para cada archivo:                                                 │
│    ├── ¿Extensión soportada?  NO → FileValidationError(unsupported) │
│    ├── ¿Tamaño > 500MB?       SÍ → FileValidationError(too_large)   │
│    ├── ¿Batch total > 2GB?    SÍ → FileValidationError(batch)       │
│    ├── ¿Más de 50 archivos?   SÍ → FileValidationError(too_many)    │
│    └── ¿Path duplicado?       SÍ → FileValidationError(duplicate)   │
│     ↓                                                               │
│  Crear ConversionFile[] con status='pending'                        │
│  Calcular sanitizedName con sanitizeFilename()                      │
│  Mostrar en FileList → appState: 'files-ready'                      │
│                                                                     │
│  FASE 2: CONVERSIÓN (Sidecar Python — al pulsar Convertir)          │
│  ──────────────────────────────────────────────────────             │
│  Input: Array de { id, path, category } + lang                      │
│     ↓                                                               │
│  Para cada archivo (secuencial):                                    │
│    ├── ¿Cancel flag activo? → emitir cancelled, PARAR               │
│    ├── Emitir file_progress(processing, progress=0)                 │
│    ├── category === 'document'?                                      │
│    │     └── markitdown.convert(path) → str                         │
│    ├── category === 'audio'?                                        │
│    │     ├── model_exists()?                                         │
│    │     │     NO → emitir model_required (Tauri pausa y descarga)  │
│    │     └── whisper.transcribe(path) → str                         │
│    ├── ¿Error? → mapear a mensaje humano → emitir file_result(error)│
│    └── ¿Éxito? → emitir file_result(completed, content=str)        │
│     ↓                                                               │
│  Emitir conversion_complete                                         │
│                                                                     │
│  FASE 3: SALIDA (Frontend — tras conversión)                        │
│  ──────────────────────────────────────────                         │
│  appState: 'results'                                                │
│  Usuario revisa preview                                             │
│     ↓                                                               │
│  ¿1 archivo completado?   → save_markdown(content, sanitizedName)  │
│  ¿2+ archivos completados?→ save_zip([{name, content}], zipName)   │
│     ↓                                                               │
│  Tauri abre diálogo nativo → usuario elige ubicación               │
│  → escribe al disco → retorna path                                  │
│  → mostrar path + botón "Mostrar en carpeta"                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Validaciones de archivos (Frontend)

### 2.1 Tabla de validaciones en orden

| # | Validación | Condición de rechazo | Error emitido |
|---|-----------|---------------------|---------------|
| 1 | Extensión soportada | `ext` no está en `SUPPORTED_EXTENSIONS` | `unsupported` |
| 2 | Tamaño individual | `file.size > 500MB` | `too_large` |
| 3 | Límite de cantidad | `files.length + new.length > 50` | `too_many_files` |
| 4 | Tamaño total del batch | `totalBytes + file.size > 2GB` | `batch_too_large` |
| 5 | Duplicado | mismo `path` ya en la lista | `duplicate` |

**Regla:** Si la validación #3 (too_many_files) falla, se para inmediatamente sin procesar más archivos. Si cualquier otra falla, se registra el error y se continúa con los siguientes archivos del batch.

### 2.2 Cómo mostrar errores de validación

- Los errores se almacenan en `useConversionStore.validationErrors`.
- Al detectar errores, el componente `ValidationErrorToast` los muestra (ver spec `06-components.md` § 21).
- Los errores se limpian automáticamente con `clearValidationErrors()` después de 5 segundos o cuando el usuario cierra el toast.
- Los archivos válidos del mismo drop **sí se añaden** aunque otros del mismo drop sean rechazados.

---

## 3. Detección de categoría por extensión

```typescript
// src/lib/fileUtils.ts

const DOCUMENT_EXTENSIONS = new Set([
  'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'docx', 'doc', 'html', 'csv'
]);

const AUDIO_EXTENSIONS = new Set([
  'mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'aac'
]);

export function getFileCategory(ext: string): FileCategory | null {
  if (DOCUMENT_EXTENSIONS.has(ext)) return 'document';
  if (AUDIO_EXTENSIONS.has(ext))    return 'audio';
  return null;
}
```

---

## 4. Algoritmo de sanitización de nombres

### 4.1 Reglas en orden de aplicación

| Paso | Operación | Ejemplo entrada → salida |
|------|-----------|--------------------------|
| 1 | Extraer stem (sin extensión original) | `"Mi Archivo.pdf"` → `"Mi Archivo"` |
| 2 | Normalizar unicode NFD (descomponer acentos) | `"á"` → `"a" + combining´` |
| 3 | Codificar a ASCII, ignorar diacríticos | `"café"` → `"cafe"` |
| 4 | Convertir a minúsculas | `"HOLA"` → `"hola"` |
| 5 | Reemplazar espacios, guiones y puntos por `_` | `"hola mundo"` → `"hola_mundo"` |
| 6 | Eliminar todo carácter no alfanumérico ni `_` | `"hola!mundo"` → `"holamundo"` |
| 7 | Colapsar `__` múltiples en uno solo | `"hola___mundo"` → `"hola_mundo"` |
| 8 | Eliminar `_` al inicio y al final | `"_hola_"` → `"hola"` |
| 9 | Si el resultado está vacío → `"archivo_sin_nombre"` | `"!@#$"` → `"archivo_sin_nombre"` |
| 10 | Añadir extensión `.md` | `"hola_mundo"` → `"hola_mundo.md"` |

### 4.2 Implementación Python (fuente de verdad — `sidecar/sanitizer.py`)

```python
import re
import unicodedata
from pathlib import Path


def sanitize_filename(original_name: str) -> str:
    """
    Convierte el nombre de un archivo a una versión segura para usar como
    nombre de archivo .md sin espacios, tildes ni caracteres especiales.
    """
    # Paso 1: Extraer stem (nombre sin extensión)
    stem = Path(original_name).stem

    # Paso 2-3: Normalizar unicode y eliminar diacríticos
    # NFD descompone "á" en "a" + combining accent
    normalized = unicodedata.normalize("NFKD", stem)
    # encode ascii ignora los combining characters
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")

    # Paso 4: Minúsculas
    lower = ascii_str.lower()

    # Paso 5: Espacios, guiones, puntos → guión bajo
    underscored = re.sub(r"[\s\-\.]+", "_", lower)

    # Paso 6: Eliminar todo lo que no sea [a-z0-9_]
    clean = re.sub(r"[^a-z0-9_]", "", underscored)

    # Paso 7: Colapsar múltiples guiones bajos
    clean = re.sub(r"_+", "_", clean)

    # Paso 8: Eliminar guiones bajos al inicio y al final
    clean = clean.strip("_")

    # Paso 9: Fallback si el resultado está vacío
    if not clean:
        clean = "archivo_sin_nombre"

    # Paso 10: Añadir extensión .md
    return f"{clean}.md"
```

### 4.3 Implementación TypeScript (frontend — `src/lib/sanitizer.ts`)

```typescript
/**
 * Replica el algoritmo Python para mostrar el sanitizedName en la lista
 * ANTES de enviar al sidecar. La fuente de verdad es Python — esta función
 * debe mantenerse sincronizada con sidecar/sanitizer.py.
 */
export function sanitizeFilename(originalName: string): string {
  // Paso 1: Extraer stem
  const stem = originalName.replace(/\.[^.]+$/, '');

  // Pasos 2-3: Normalizar unicode y eliminar diacríticos
  const normalized = stem
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, ''); // Eliminar combining characters

  const result = normalized
    .toLowerCase()                        // Paso 4
    .replace(/[\s\-.]+/g, '_')           // Paso 5
    .replace(/[^a-z0-9_]/g, '')          // Paso 6
    .replace(/_+/g, '_')                  // Paso 7
    .replace(/^_|_$/g, '');              // Paso 8

  return `${result || 'archivo_sin_nombre'}.md`; // Pasos 9-10
}
```

### 4.4 Tabla de ejemplos completa

| Nombre original | Nombre sanitizado |
|----------------|------------------|
| `Mi Presentación 2024.pptx` | `mi_presentacion_2024.md` |
| `Reporte Anual (Final).pdf` | `reporte_anual_final.md` |
| `audio grabación #3.mp3` | `audio_grabacion_3.md` |
| `Análisis Q1 — Versión 2.xlsx` | `analisis_q1_version_2.md` |
| `DOCUMENTO EN MAYÚSCULAS.docx` | `documento_en_mayusculas.md` |
| `file.with.dots.inside.pdf` | `file_with_dots_inside.md` |
| `!@#$%.xlsx` | `archivo_sin_nombre.md` |
| `über die Straße.pdf` | `uber_die_strae.md` |
| `résumé final v3.docx` | `resume_final_v3.md` |
| `    espacios al inicio.mp3` | `espacios_al_inicio.md` |
| `___guiones___múltiples___.csv` | `guiones_multiples.md` |
| `archivo (1).pdf` | `archivo_1.md` |
| `informe2024.pdf` | `informe2024.md` |
| `datos_ventas.Q1.xlsx` | `datos_ventas_q1.md` |
| `.oculto.pdf` | `oculto.md` |
| `123.pdf` | `123.md` |
| `a.pdf` | `a.md` |

---

## 5. Formato del output markdown por tipo de archivo

### 5.1 Documentos (markitdown)

markitdown devuelve el texto ya en formato markdown. No modificar el output — usarlo tal cual. El resultado puede incluir:
- Encabezados (`#`, `##`, etc.)
- Tablas (especialmente de Excel)
- Listas
- Texto en negrita/cursiva
- Párrafos de texto simple

**Si markitdown devuelve un string vacío o solo whitespace:** lanzar `ValueError("No se encontró texto en el archivo")`.

### 5.2 Audio (Whisper)

El resultado de Whisper es texto plano. Formatearlo así:

```markdown
# Transcripción: {stem_original}

> Transcripción generada automáticamente con Whisper (modelo: base)
> Archivo original: {nombre_original_con_extension}

---

{texto_transcrito}
```

Donde:
- `{stem_original}` = nombre del archivo sin extensión (el original, no el sanitizado)
- `{nombre_original_con_extension}` = nombre completo original
- `{texto_transcrito}` = el texto que retornó Whisper, tal cual

**Si Whisper retorna texto vacío:** lanzar `ValueError("audio_too_short")`.

---

## 6. Gestión del modelo Whisper

### 6.1 Flujo de verificación antes de transcribir

```
Al iniciar la app (AppShell):
  → invoke('check_whisper_model')
  → useConversionStore._setModelAvailable(bool)

Al pulsar "Convertir" con archivos de audio:
  → Si whisperModelAvailable: proceder normalmente
  → Si no: Tauri/sidecar emite evento especial (ver 6.2)
```

### 6.2 Flujo cuando el modelo no está disponible

```
1. Usuario pulsa "Convertir"
2. Frontend → invoke('start_conversion', { files, lang })
3. Sidecar llega al primer archivo de audio
4. Sidecar verifica model_exists() → False
5. Sidecar NO emite error — en su lugar espera el comando 'download_model'
   [El flujo de pausa/reanudación se implementa en el sidecar manteniendo
    el estado y esperando el siguiente comando en stdin]

ALTERNATIVA MÁS SIMPLE (recomendada para v1):
1. Frontend verifica whisperModelAvailable antes de invocar start_conversion
2. Si hay audios y el modelo no está:
   a. Mostrar WhisperModelModal
   b. Si usuario confirma: invoke('download_whisper_model')
   c. Esperar evento 'model:download-complete'
   d. Luego invocar start_conversion normalmente
3. Si usuario cancela el modal: no iniciar la conversión
```

**Implementación recomendada (opción alternativa) en `useConversionStore.startConversion()`:**

```typescript
startConversion: async (lang) => {
  const { files, whisperModelAvailable, hasAudioFiles } = get();

  // Si hay audios y el modelo no está listo, abrir el modal
  // El modal y su flujo se gestionan en App.tsx
  if (hasAudioFiles && !whisperModelAvailable) {
    // Señalar al UI que debe mostrar el modal antes de continuar
    // Esto se maneja con un estado temporal showWhisperModal en el store
    // o pasando una callback desde App.tsx
    return; // No iniciar — el modal se encarga de llamar startConversion de nuevo
  }

  // ... resto de la lógica
}
```

### 6.3 Ruta del modelo en disco

| OS | Ruta |
|----|------|
| macOS | `~/Library/Application Support/Markify/models/whisper/base.pt` |
| Windows | `%APPDATA%\Markify\models\whisper\base.pt` |
| Linux | `~/.config/Markify/models/whisper/base.pt` |

En el contexto del sidecar empaquetado con PyInstaller: `{directorio del binario}/models/whisper/base.pt`.

### 6.4 Verificación de integridad del modelo

La verificación es simple: el archivo existe Y tiene tamaño > 100MB. No se verifica el hash SHA256 en v1 (aceptable para uso personal).

```python
def model_exists() -> bool:
    model_file = get_model_path() / "base.pt"
    if not model_file.exists():
        return False
    size_mb = model_file.stat().st_size / (1024 * 1024)
    return size_mb > 100
```

---

## 7. Manejo de cancelación

### 7.1 Cuándo puede cancelar el usuario

Solo durante `appState === 'processing'`. El botón "Cancelar" está visible únicamente en ese estado.

### 7.2 Qué pasa al cancelar

1. Frontend: `isCancelling = true`, botón queda disabled.
2. Frontend: `invoke('cancel_conversion')` → Rust escribe `{"command": "cancel"}` al sidecar.
3. Sidecar: activa `_cancel_flag` (threading.Event).
4. Sidecar: al inicio del loop del siguiente archivo, detecta el flag y emite `conversion_cancelled`.
5. **El archivo que está procesando en ese momento termina** — no se puede interrumpir mid-process sin corrupción.
6. Rust: recibe `conversion_cancelled` del sidecar, emite evento `conversion:cancelled` al frontend.
7. Frontend: `_handleConversionCancelled()` → `appState = 'files-ready'`, `isCancelling = false`.
8. Los archivos que ya completaron (con éxito o error) mantienen su status. Los que no se procesaron vuelven a `pending`.

### 7.3 Qué NO pasa al cancelar

- No se descarta el contenido de archivos ya completados (se mantiene en memoria).
- No se genera ningún archivo de salida — el usuario debe volver a convertir.
- El sidecar sigue corriendo (no se mata el proceso).

---

## 8. Procesamiento secuencial vs. paralelo

**v1 es siempre secuencial.** Un archivo a la vez.

**Razones:**
1. Whisper usa mucha memoria RAM — dos en paralelo podría crashear en sistemas con 8GB.
2. Simplifica enormemente el manejo de cancelación y errores.
3. markitdown es rápido — no hay ganancia real en paralelizar documentos.

**Futuro (v2):** paralelizar solo documentos (no audio) con un pool de workers limitado a 2.

---

## 9. Límites y consideraciones de rendimiento

| Escenario | Comportamiento esperado |
|-----------|------------------------|
| PDF de 1 página | < 1 segundo |
| PDF de 100 páginas | 5-15 segundos |
| PPTX con 50 slides | 3-8 segundos |
| XLSX con 10.000 filas | 2-10 segundos |
| MP3 de 1 minuto | 15-30 segundos (CPU moderna) |
| MP3 de 60 minutos | 10-20 minutos (CPU moderna) |
| PDF con contraseña | < 1 segundo (falla rápido) |
| PDF sin texto (solo imágenes) | < 2 segundos (devuelve vacío) |

**Nota sobre audios largos:** La UI nunca hace timeout. El usuario puede esperar. La barra de progreso muestra shimmer hasta que llega progreso real del sidecar. Para audios > 30 minutos, la UX es aceptable en v1.
