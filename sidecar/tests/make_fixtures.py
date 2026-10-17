# sidecar/tests/make_fixtures.py
"""
Genera PDFs pequeños (< 100 KB) para las pruebas del pipeline de PDF. Nada se commitea: lo usa conftest.py.

Uso manual: python tests/make_fixtures.py <carpeta>
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAGE_PX = (1240, 1754)  # A4 a 150 DPI
A4 = (595.27, 841.89)   # puntos
FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

ES_LINES = [
    "La conversión de documentos escaneados",
    "Año 2024: niños, canción y ¿más pingüinos?",
    "¡Atención! El corazón de la información",
    "está en cada línea del párrafo.",
]
EN_LINES = [
    "Markify converts scanned documents",
    "Hello world 2024: local text recognition",
    "Every page is processed one at a time",
    "and nothing leaves your computer.",
]


def _font(size: int):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size=size)


def text_page(lines: list[str], size: int = 54) -> Image.Image:
    """Página A4 a 150 DPI con `lines` en negro sobre blanco."""
    img = Image.new("RGB", PAGE_PX, "white")
    draw, font = ImageDraw.Draw(img), _font(size)
    for i, line in enumerate(lines):
        draw.text((120, 160 + i * 110), line, font=font, fill="black")
    return img


def scan_pdf(path: Path, pages: list[list[str]]) -> None:
    imgs = [text_page(p) for p in pages]
    imgs[0].save(path, format="PDF", resolution=150, save_all=True, append_images=imgs[1:])


def _reportlab_pdf(path: Path, pages, **canvas_kw) -> None:
    """`pages`: lista de callables(canvas) que dibujan una página (vacío = página en blanco)."""
    from reportlab.lib.pagesizes import A4 as RL_A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=RL_A4, **canvas_kw)
    for draw in pages:
        draw(c)
        c.showPage()
    c.save()


def _text_page_draw(title: str):
    def draw(c):
        c.setFont("Helvetica", 14)
        for i in range(12):
            c.drawString(72, 760 - i * 24, f"{title}: línea {i + 1} con texto nativo suficiente para clasificar.")
    return draw


def _image_page_draw(img_path: Path):
    def draw(c):
        c.drawImage(str(img_path), 0, 0, width=A4[0], height=A4[1])
    return draw


def make_fixtures(out: Path) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    p = {name: out / f"{name}.pdf" for name in (
        "text", "text_multi", "text_table", "scan_es", "scan_en", "scan_text_layer", "scan_mixed",
        "encrypted", "truncated", "blank", "bad_page",
    )}
    es_png, en_png = out / "es.png", out / "en.png"
    text_page(ES_LINES).save(es_png)
    text_page(EN_LINES).save(en_png)

    _reportlab_pdf(p["text"], [_text_page_draw("Uno")])
    _reportlab_pdf(p["text_multi"], [_text_page_draw(f"Pág {i}") for i in range(1, 6)])

    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    table = Table([["Producto", "Cantidad", "Precio"], ["Lápiz", "10", "1.50"], ["Cuaderno", "4", "3.20"], ["Goma", "7", "0.80"]])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    SimpleDocTemplate(str(p["text_table"])).build([table])

    scan_pdf(p["scan_es"], [ES_LINES])
    scan_pdf(p["scan_en"], [EN_LINES])

    def scan_with_layer(c):  # imagen de página completa + capa de texto invisible (render mode 3)
        c.drawImage(str(es_png), 0, 0, width=A4[0], height=A4[1])
        t = c.beginText(72, 700)
        t.setTextRenderMode(3)
        t.textLine("Capa de texto previa con suficientes caracteres para mandar sobre el OCR.")
        c.drawText(t)

    _reportlab_pdf(p["scan_text_layer"], [scan_with_layer])
    # texto, escaneada, en blanco, texto
    _reportlab_pdf(p["scan_mixed"], [_text_page_draw("Intro"), _image_page_draw(es_png), lambda c: None, _text_page_draw("Fin")])

    from reportlab.lib.pdfencrypt import StandardEncryption

    _reportlab_pdf(p["encrypted"], [_text_page_draw("Secreto")], encrypt=StandardEncryption("user", ownerPassword="owner"))
    data = p["text"].read_bytes()
    p["truncated"].write_bytes(data[: len(data) // 2])
    _reportlab_pdf(p["blank"], [lambda c: None])

    # Escaneada / escaneada rota / escaneada: la página 2 apunta a un objeto de página inexistente.
    _reportlab_pdf(p["bad_page"], [_image_page_draw(es_png), _image_page_draw(en_png), _image_page_draw(es_png)])
    _break_page(p["bad_page"], 2)
    return p


def _break_page(path: Path, page_no: int) -> None:
    """Invalida el tipo del objeto /Page número `page_no` para que pdfium no pueda cargarla."""
    data = path.read_bytes()
    marker = b"/Type /Page\n"
    pos = -1
    for _ in range(page_no):
        pos = data.index(marker, pos + 1)
    path.write_bytes(data[:pos] + b"/Type /Pxge\n" + data[pos + len(marker):])


if __name__ == "__main__":
    for name, f in make_fixtures(Path(sys.argv[1])).items():
        print(f"{name}: {f.stat().st_size} bytes")
