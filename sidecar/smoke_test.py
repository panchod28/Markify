# sidecar/smoke_test.py
"""
Smoke test del sidecar compilado (PyInstaller --onedir). Lo ejecuta CI antes de empaquetar la app.

Uso: python smoke_test.py [--dir <carpeta>] [--max-seconds 3]

Comprueba que el binario arranca, responde al protocolo (stdout = solo JSON) y convierte un archivo,
y que el arranque posterior al primero cumple el presupuesto.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_DIR = Path(__file__).parent.parent / "src-tauri" / "binaries" / "markify-sidecar"
FIRST_RUN_TIMEOUT_S = 900  # el primer arranque puede tardar minutos (verificación del SO / antivirus)


def run_sidecar(exe: Path, messages: list[dict], timeout: int) -> tuple[list[dict], float]:
    """Envía mensajes por stdin, cierra stdin y devuelve (mensajes JSON de stdout, segundos)."""
    stdin = "".join(json.dumps(m) + "\n" for m in messages)
    start = time.monotonic()
    proc = subprocess.run(
        [str(exe)], input=stdin, capture_output=True, text=True, encoding="utf-8",
        timeout=timeout,
    )
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        raise AssertionError(f"exit code {proc.returncode}\n--- stderr ---\n{proc.stderr[-2000:]}")
    out = []
    for line in proc.stdout.splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            raise AssertionError(f"stdout contiene texto que no es JSON: {line!r}")
    return out, elapsed


def check_model(exe: Path, timeout: int) -> float:
    out, elapsed = run_sidecar(exe, [{"id": "smoke", "command": "check_model", "payload": {}}], timeout)
    assert any(m.get("type") == "model_status" for m in out), f"sin model_status: {out}"
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--max-seconds", type=float, default=3.0)
    args = parser.parse_args()

    exe = args.dir / ("markify-sidecar.exe" if sys.platform == "win32" else "markify-sidecar")
    assert exe.exists(), f"no existe {exe}; ejecuta `python build.py`"

    first = check_model(exe, FIRST_RUN_TIMEOUT_S)
    print(f"1er arranque: {first:.1f}s (informativo)")

    # El mejor de dos arranques posteriores: tolera un pico puntual del runner.
    later = min(check_model(exe, 120) for _ in range(2))
    print(f"arranque posterior: {later:.1f}s (máx {args.max_seconds}s)")
    assert later <= args.max_seconds, f"arranque {later:.1f}s > {args.max_seconds}s"

    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "smoke.csv"
        csv.write_text("a,b\n1,2\n", encoding="utf-8")
        out, _ = run_sidecar(exe, [{
            "id": "smoke", "command": "convert",
            "payload": {"lang": "en", "files": [{"id": "f1", "path": str(csv), "category": "document"}]},
        }], 120)
    result = next((m for m in out if m.get("type") == "file_result"), None)
    assert result and result["payload"]["status"] == "completed", f"conversión falló: {out}"
    assert "| a | b |" in result["payload"]["markdownContent"], result["payload"]["markdownContent"]
    assert out[-1].get("type") == "conversion_complete", out

    print("OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
