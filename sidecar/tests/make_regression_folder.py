# sidecar/tests/make_regression_folder.py
"""
Crea una carpeta con UN archivo de cada formato que acepta Markify (src/types/index.ts) para probar la regresión
completa desde la UI: seleccionar todo, convertir y guardar el ZIP. Solo macOS (usa `say`, `afconvert`, `textutil`
y ffmpeg para el audio/vídeo); lo que no se pueda generar se avisa y se omite.

Uso: python tests/make_regression_folder.py <carpeta>
Con --expected escribe también <carpeta>/../expected.json (texto que debe aparecer en cada conversión).
"""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parent)]
from make_fixtures import ES_LINES, text_page  # noqa: E402

SPEECH = "Hello, this is a test of the audio transcription."
EXPECTED: dict[str, str] = {}   # archivo -> subcadena (en minúsculas) que debe aparecer en el .md


def run(*cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def expect(name: str, text: str):
    EXPECTED[name] = text.lower()


def documents(d: Path):
    # --- csv / html
    (d / "datos.csv").write_text("producto,cantidad\nLápiz,10\nCuaderno,4\n", encoding="utf-8")
    expect("datos.csv", "| lápiz | 10 |")
    html = "<html><body><h1>Título HTML</h1><p>Párrafo con ñandú y <b>negrita</b>.</p><ul><li>uno</li><li>dos</li></ul></body></html>"
    (d / "pagina.html").write_text(html, encoding="utf-8")
    expect("pagina.html", "título html")

    # --- pdf con texto (y tabla)
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    c = canvas.Canvas(str(d / "pdf con texto.pdf"), pagesize=A4)
    c.setFont("Helvetica", 14)
    for i in range(1, 8):
        c.drawString(72, 780 - i * 24, f"Línea {i} de un PDF con texto nativo para la prueba de regresión.")
    c.showPage()
    c.save()
    expect("pdf con texto.pdf", "línea 7 de un pdf")
    t = Table([["Producto", "Cantidad"], ["Lápiz", "10"], ["Goma", "7"]])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    SimpleDocTemplate(str(d / "pdf con tabla.pdf")).build([t])
    expect("pdf con tabla.pdf", "goma")

    # --- docx (mínimo, sin dependencias)
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Informe Word</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>Documento .docx con ñandú, canción y ¿preguntas?</w:t></w:r></w:p></w:body></w:document>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" '
          'ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override '
          'PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship '
            'Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(d / "documento.docx", "w") as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
    expect("documento.docx", "informe word")

    # --- xlsx / pptx
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventas"
    ws.append(["Mes", "Total"])
    ws.append(["Enero", 1200])
    ws.append(["Febrero", 980])
    wb.save(d / "hoja.xlsx")
    expect("hoja.xlsx", "enero")

    from pptx import Presentation
    p = Presentation()
    s = p.slides.add_slide(p.slide_layouts[1])
    s.shapes.title.text = "Presentación de prueba"
    s.placeholders[1].text = "Punto uno\nPunto dos con ñ"
    p.save(d / "presentacion.pptx")
    expect("presentacion.pptx", "presentación de prueba")

    # --- formatos antiguos
    try:
        import xlwt
        w = xlwt.Workbook()
        sh = w.add_sheet("Hoja1")
        for r, row in enumerate([["Mes", "Total"], ["Marzo", 500], ["Abril", 700]]):
            for col, v in enumerate(row):
                sh.write(r, col, v)
        w.save(str(d / "hoja antigua.xls"))
        expect("hoja antigua.xls", "marzo")
    except ImportError:
        print("aviso: sin xlwt (pip install xlwt), se omite .xls")
    (d / "_tmp.html").write_text("<html><body><h1>Documento Word antiguo</h1><p>Contenido del .doc con ñ.</p></body></html>", encoding="utf-8")
    try:
        run("textutil", "-convert", "doc", str(d / "_tmp.html"), "-output", str(d / "documento antiguo.doc"))
        # .doc ya no se convierte: la app lo rechaza con "Formato antiguo…" (no entra en expected.json)
    except Exception as e:
        print("aviso: no se pudo generar .doc:", e)
    (d / "_tmp.html").unlink()
    # .ppt: no hay forma de generarlo en macOS (PowerPoint para Mac ya no guarda en el formato 97-2003): añade uno propio a la carpeta.
    print("aviso: no se genera .ppt (formato antiguo de PowerPoint); copia uno real a la carpeta si quieres probarlo")


def media(d: Path):
    tmp = d / "_voz.aiff"
    run("say", "-v", "Samantha", "-o", str(tmp), SPEECH)
    run("afconvert", "-f", "WAVE", "-d", "LEI16@16000", str(tmp), str(d / "audio.wav"))
    wav = str(d / "audio.wav")
    run("ffmpeg", "-y", "-i", wav, "-c:a", "libmp3lame", str(d / "audio.mp3"))
    run("ffmpeg", "-y", "-i", wav, "-c:a", "aac", str(d / "audio.m4a"))
    run("ffmpeg", "-y", "-i", wav, "-c:a", "aac", "-f", "adts", str(d / "audio.aac"))
    run("ffmpeg", "-y", "-i", wav, "-c:a", "flac", str(d / "audio.flac"))
    run("ffmpeg", "-y", "-i", wav, "-c:a", "libopus", "-f", "ogg", str(d / "audio.ogg"))
    run("ffmpeg", "-y", "-i", wav, "-c:a", "libopus", "-f", "webm", str(d / "audio.webm"))
    # vídeo con pista de voz
    run("ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=320x240:d=6", "-i", wav, "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(d / "video.mp4"))
    tmp.unlink()
    for n in ("audio.wav", "audio.mp3", "audio.m4a", "audio.aac", "audio.flac", "audio.ogg", "audio.webm", "video.mp4"):
        expect(n, "audio transcription")


def images(d: Path):
    img = text_page(ES_LINES, size=54, px=(1000, 700))
    for ext, fmt in (("png", "PNG"), ("jpg", "JPEG"), ("jpeg", "JPEG"), ("webp", "WEBP"), ("bmp", "BMP"), ("tif", "TIFF"), ("tiff", "TIFF")):
        img.save(d / f"imagen.{ext}", format=fmt)
        expect(f"imagen.{ext}", "conversión")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    documents(out)
    media(out)
    images(out)
    (out.parent / "expected.json").write_text(json.dumps(EXPECTED, ensure_ascii=False, indent=1), encoding="utf-8")
    files = sorted(p.name for p in out.iterdir())
    print(f"{len(files)} archivos en {out}:\n  " + "\n  ".join(files))


if __name__ == "__main__":
    main()
