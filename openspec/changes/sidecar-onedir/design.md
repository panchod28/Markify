## Context

- `sidecar/build.py` ejecuta PyInstaller con `--onefile` y escribe `src-tauri/binaries/markify-sidecar-<triple>[.exe]`; `tauri.conf.json` lo declara en `bundle.externalBin`; `spawn_sidecar` lo lanza con `app.shell().sidecar("markify-sidecar")`.
- En `--onefile`, el bootloader extrae todo a un directorio temporal nuevo en cada arranque. En macOS cada librería recién escrita se vuelve a evaluar al cargarla.
- **Mediciones** (macOS arm64, mismo código con torch/whisper/markitdown/magika, sin python-pptx/openpyxl/xlrd porque el `.venv` local no los tiene, comando `check_model` por stdin):

| Variante | Primer arranque | Arranques siguientes | Tamaño |
|---|---|---|---|
| `--onefile` (binario actual) | 41–46 s | 41–46 s (siempre) | 238 MB |
| `--onedir` | 25.7 s | **1.4 s** | 570 MB descomprimido, 180 MB `tar.gz`, 2 450 archivos, ruta relativa más larga 103 caracteres |

- `AppShell` llama a `checkWhisperModel()` al montar; en Rust `check_whisper_model` espera 5 s y el store no captura el error. Con el arranque actual ese timeout es muy probable en cada apertura.
- La carpeta temporal de `--onefile` desaparece al salir limpiamente; si el proceso se mata, queda huérfana (570 MB cada vez).
- El `.venv` local no reproduce el build de CI sin ajustes (faltan `python-pptx`/`openpyxl`/`xlrd`; con numpy 2.4 `--collect-submodules numpy` falla y hay que colectar `numpy._core`/`numpy.lib` y añadir `setuptools/_vendor` al path). Se detectó al medir; no se corrige aquí salvo lo que el nuevo `build.py` necesite.

## Goals / Non-Goals

**Goals**
- Arranque del sidecar ≤ 3 s tras la primera ejecución; sin penalización recurrente por extracción.
- Mantener el protocolo, los eventos, `SidecarState` y la lógica de conversión intactos.
- Mismo comportamiento en macOS arm64 y Windows x64, en `tauri dev` y en el instalador.

**Non-Goals**
- Firmar/notarizar la app (hoy no se hace; queda anotado como requisito futuro para `_internal`).
- Mover el modelo Whisper a un directorio de datos de usuario (problema preexistente: se guarda junto al ejecutable).
- Reducir el tamaño del sidecar (torch), nuevas plataformas (Linux, Intel Mac), auto-actualización.
- Eliminar la espera del primer arranque en macOS (es verificación del sistema operativo).

## Decisions

### D1. PyInstaller `--onedir` con `_internal/` por defecto
`build.py` cambia `--onefile` por `--onedir` (`--contents-directory` por defecto) y escribe en `src-tauri/binaries/markify-sidecar/` (sin triple: cada runner compila para su propia plataforma; el triple solo se usa para nombrar el artefacto de CI). Se limpia el destino antes de compilar para no arrastrar archivos viejos. Se conserva el resto de flags y `hook-markitdown.py`.

*Alternativa descartada — mantener `--onefile` y mitigar con importaciones perezosas*: no ataca la causa (la extracción + verificación ocurre antes de ejecutar Python) y OpenCV lo empeora.
*Alternativa descartada — `--onefile` con `--runtime-tmpdir` fijo*: reutiliza el directorio pero PyInstaller lo vuelve a extraer/validar y no es portable entre plataformas.

### D2. Integración con Tauri: ruta por plataforma, lanzamiento desde Rust (decidido tras el spike en macOS)

Se descarta `externalBin`. El ejecutable se lanza desde Rust con `app.shell().command(ruta)` (devuelve el mismo `(rx, CommandChild)`, así que `SidecarState`, el bucle de eventos, `write_to_sidecar` y el resto no cambian). La **ruta** y la **forma de incluir la carpeta** dependen de dónde se ejecute:

| Contexto | Cómo se incluye | Ruta que resuelve `spawn_sidecar` |
|---|---|---|
| macOS instalado | `bundle.macOS.files` en `tauri.macos.conf.json`: `{"Resources/sidecar": "binaries/markify-sidecar"}` | `Contents/Resources/sidecar/markify-sidecar` (`BaseDirectory::Resource`) |
| Windows instalado | `bundle.resources` en `tauri.windows.conf.json`: `{"binaries/markify-sidecar/": "sidecar/"}` | `<recursos>/sidecar/markify-sidecar.exe` (`BaseDirectory::Resource`) — **pendiente de verificar (1.4)** |
| `tauri dev` (ambas) | no se copia nada | `CARGO_MANIFEST_DIR/binaries/markify-sidecar/…` (`cfg!(debug_assertions)`) |

**Por qué `macOS.files` y no `resources` en macOS**: `bundle.resources` **desreferencia los symlinks** (PyInstaller deja 10 en macOS, entre ellos `libtorch_cpu.dylib` de 247 MB); el `.app` pasó de 580 MB a 857 MB y el `tar.gz` de 180 MB a 246 MB. `macOS.files` los conserva. Quitar los symlinks a mano rompe torch (`dlopen` falla), así que no es alternativa.

*Alternativa descartada — Opción B (`externalBin` + `_internal` al lado)*: dos configuraciones por plataforma igualmente, más dependencia de dónde coloca Tauri cada pieza, y no resolvía el problema de symlinks.
*Alternativa descartada — empaquetar la carpeta como un único `.tar` y extraerla en el primer arranque*: más código Rust, otra espera de primer arranque y una copia más en disco.

**Verificado en el spike (macOS arm64, app real compilada)**: (1) `shell().command()` desde Rust funciona sin permiso/scope en `capabilities` (el scope solo aplica a invocaciones desde JS); (2) el bit de ejecución se conserva (755); (3) el sidecar arranca como hijo de la app y responde `check_model` en 1.4 s desde la ruta del bundle; (4) `tauri dev` lanza el sidecar desde `src-tauri/binaries/markify-sidecar/` sin copiar los 570 MB a `target/`; (5) al cerrar la app no quedan procesos del sidecar. **Sin verificar**: Windows (rutas del instalador, MAX_PATH, antivirus), una conversión completa desde la UI.

### D3. Errores de arranque claros
`spawn_sidecar` devuelve un error con la **ruta buscada** si el ejecutable no existe o no se puede lanzar (hoy el mensaje es "Sidecar no encontrado: …" sin ruta). No hay modo dual onefile/onedir (YAGNI).

### D4. Primer arranque lento: timeout, no "listo"
`check_whisper_model` pasa de 5 s a 60 s (constante con nombre) porque el primer arranque en macOS puede tardar ~26 s; `useConversionStore.checkWhisperModel` captura el error y deja el estado anterior (sin mostrar el modal de descarga por error). No se añade un mensaje `ready` en el protocolo: es más superficie para el mismo efecto. Si más adelante se quiere mostrar "preparando el motor…" en la UI, es un change aparte.

### D5. CI: `tar` en lugar de archivo suelto
`upload-artifact` aplana permisos y symlinks (10 symlinks en macOS). El job `build-sidecar` crea `sidecar-<triple>.tar` (`tar` existe en runners macOS y Windows), `build-app` lo extrae en `src-tauri/binaries/` (se elimina el `chmod` suelto). Un paso de *smoke test* ejecuta el sidecar compilado, le envía `check_model` y verifica `model_status`; imprime el tiempo de la segunda ejecución y falla si supera el presupuesto.

### D6. Presupuestos
- Arranque posterior al primero (hasta `model_status`): **≤ 3 s** (medido 1.4 s).
- Primer arranque tras instalar: puede ser largo en macOS (medido 26–48 s según build); no debe producir errores visibles en la UI.
- Tamaño instalado: ≤ 900 MB en disco. Medido con el build completo (`markitdown[all]`, torch 2.14): carpeta 850 MB, `.app` 860 MB con 28 symlinks conservados; torch 460 MB, llvmlite 123 MB, onnxruntime 70 MB y `speech_recognition` 43 MB son lo más pesado. (La cifra de 570 MB de la tabla de Context era un build sin extras ofimáticos/audio); instalador comprimido ≤ onefile +20 %. Medido like-for-like (mismo entorno limpio, DMG UDZO con `hdiutil`): `--onefile` 305 MB vs `--onedir` **357 MB (+52 MB, +17 %)**; el DMG del release anterior (build de junio, dependencias distintas) pesaba 256 MB, la diferencia restante viene de las dependencias actuales (torch 2.14, `markitdown[all]`), no del empaquetado.

## Risks / Trade-offs

- **[Rutas largas en Windows]** `_internal\torch\...` bajo `C:\Program Files\Markify\sidecar\` → ruta relativa máx. 103 + prefijo ≈ 150 < 260; verificar en el instalador real y que MSI/NSIS no fallen con ~2 450 archivos.
- **[Instalación más lenta / antivirus]** miles de archivos se escanean la primera vez en Windows → medir tiempo de instalación y primer arranque en una VM limpia; documentarlo.
- **[Firmado futuro]** si algún día se firma/notariza en macOS, `Resources/sidecar/**` (Mach-O sueltos, con symlinks) debe firmarse explícitamente. Se anota como requisito, no se resuelve aquí.
- **[Primer arranque de ~26 s en macOS]** inevitable (verificación del SO); con `onefile` ocurría siempre. Mitigado por D4; no se mejora la percepción visual aquí.
- **[Contribuidores con binarios viejos]** `src-tauri/binaries/` ahora es una carpeta → CONTRIBUTING lo explica y `build.py` limpia el destino.
- **[Actualizaciones de la app]** al reemplazar el bundle se borra `models/whisper` guardado junto al ejecutable (preexistente con `onefile`); fuera de alcance, se propone como change aparte.
- **[Reproducibilidad del build local]** el `.venv` actual no compila sin ajustes; `build.py` debe incluir los flags necesarios para numpy ≥ 2.4 y `requirements.txt` debe listar los extras (`markitdown[all]`/`pdf`, `python-pptx`, `openpyxl`, `xlrd`) — ver tareas.

## Migration Plan

1. Spike de integración (Opción A vs B) en macOS y Windows con el sidecar real.
2. Cambios de build + Rust + config en una sola rama; verificación manual en `tauri dev` y en instalador de ambas plataformas.
3. Release interno; si el instalador falla en alguna plataforma, revertir el commit (no hay modo dual ni migración de datos de usuario).

## Open Questions

1. ~~Opción A vs B~~: decidido (A, ver D2, con `macOS.files` en macOS).
2. ¿Quieres que este change corrija también el `.venv`/`requirements.txt` (extras faltantes, numpy 2.4)? Por defecto **sí**, mínimo necesario para que `build.py` funcione desde un entorno limpio.
3. ¿Mostrar en la UI un estado "preparando el motor" durante el primer arranque? Por defecto **no** (change aparte).
