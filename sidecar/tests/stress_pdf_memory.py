# sidecar/tests/stress_pdf_memory.py
"""
Prueba de memoria y cancelación (tarea 3.10 del change add-ocr-image-pdf-support). No la recoge pytest.

Uso: python tests/stress_pdf_memory.py [páginas=200] [--max-rss-mb 1500]
Genera un PDF escaneado sintético, lo convierte con el OCR real, muestrea el RSS tras cada página y
comprueba (1) pico <= tope, (2) sin crecimiento lineal con las páginas, (3) cancelación en < 1 página.
"""

import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parent.parent), str(Path(__file__).parent)]

from make_fixtures import A4, ES_LINES, text_page  # noqa: E402
from ocr.pdf_pipeline import convert_pdf  # noqa: E402


def rss_mb() -> float:
    """Memoria residente del proceso (working set en Windows)."""
    import os
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                               "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                               "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

        c = Counters()
        c.cb = ctypes.sizeof(c)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        assert ctypes.windll.kernel32.K32GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb), "GetProcessMemoryInfo falló"
        return c.WorkingSetSize / 1024 / 1024
    return int(subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())]).split()[0]) / 1024


def make_pdf(path: Path, pages: int) -> None:
    from reportlab.lib.pagesizes import A4 as RL_A4
    from reportlab.pdfgen import canvas

    png = path.with_suffix(".png")
    text_page(ES_LINES).save(png)
    c = canvas.Canvas(str(path), pagesize=RL_A4)
    for _ in range(pages):
        c.drawImage(str(png), 0, 0, width=A4[0], height=A4[1])  # reportlab reutiliza el mismo XObject
        c.showPage()
    c.save()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pages = int(args[0]) if args else 200
    max_rss = float(sys.argv[sys.argv.index("--max-rss-mb") + 1]) if "--max-rss-mb" in sys.argv else 1500

    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "big.pdf"
        make_pdf(pdf, pages)
        import platform
        print(f"{platform.platform()} | {platform.processor() or platform.machine()} | Python {platform.python_version()}")
        print(f"PDF: {pages} páginas, {pdf.stat().st_size / 1024:.0f} KB")

        samples, stamps = [], []
        t0 = time.monotonic()

        def on_progress(pct):
            samples.append(rss_mb())
            stamps.append(time.monotonic())

        result = convert_pdf(str(pdf), threading.Event(), on_progress)
        total = time.monotonic() - t0
        assert result.markdown.count("conversión") == pages, f"se esperaban {pages} páginas con texto"
        quarter = max(1, len(samples) // 4)
        first, last = max(samples[:quarter]), max(samples[-quarter:])
        print(f"tiempo: {total:.0f}s ({total / pages:.2f} s/página)")
        print(f"RSS: pico {max(samples):.0f} MB; máx. 1er cuarto {first:.0f} MB, máx. último cuarto {last:.0f} MB")
        assert max(samples) <= max_rss, f"RSS pico {max(samples):.0f} MB > {max_rss:.0f} MB"
        assert last <= first * 1.15 + 50, "el RSS crece con el número de páginas"

        # Cancelación: se activa en un instante arbitrario; debe devolver antes de terminar otra página.
        cancel, started = threading.Event(), time.monotonic()
        per_page = total / pages
        timer = threading.Timer(per_page * 5.37, cancel.set)
        timer.start()
        out = convert_pdf(str(pdf), cancel, lambda p: None)
        latency = time.monotonic() - started - per_page * 5.37
        print(f"cancelación: latencia {latency:.2f}s (página ≈ {per_page:.2f}s)")
        assert out.markdown == "" and latency < per_page * 1.2, "la cancelación tardó más de una página"
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
