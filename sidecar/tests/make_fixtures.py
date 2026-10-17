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


def text_page(lines: list[str], size: int = 54, px: tuple[int, int] = PAGE_PX) -> Image.Image:
    """Imagen (por defecto A4 a 150 DPI) con `lines` en negro sobre blanco."""
    img = Image.new("RGB", px, "white")
    draw, font = ImageDraw.Draw(img), _font(size)
    for i, line in enumerate(lines):
        draw.text((min(120, px[0] // 10), min(160, px[1] // 8) + i * int(size * 2), ), line, font=font, fill="black")
    return img


DIAGRAM_LINES = ["Diagrama de flujo", "Entrada -> Proceso -> Salida", "Fase uno y fase dos"]
COL_LEFT = ["Primera columna arriba", "sigue el texto de la izquierda", "y termina aqui abajo"]
COL_RIGHT = ["Segunda columna arriba", "sigue el texto de la derecha", "y cierra el documento"]


def two_column_page() -> Image.Image:
    """Dos columnas desiguales (la derecha más corta) con un pie de página centrado."""
    img = Image.new("RGB", PAGE_PX, "white")
    draw, font = ImageDraw.Draw(img), _font(30)
    for i, (l, r) in enumerate(zip(COL_LEFT, COL_RIGHT)):
        draw.text((100, 160 + i * 70), l, font=font, fill="black")
        draw.text((640, 160 + i * 70), r, font=font, fill="black")
    draw.text((520, 1650), "Pagina 1 de 1", font=font, fill="black")
    return img


def scan_pdf(path: Path, pages: list[list[str]]) -> None:
    scan_pdf_images(path, [text_page(p) for p in pages])


def scan_pdf_images(path: Path, imgs: list[Image.Image]) -> None:
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
        "encrypted", "truncated", "blank", "bad_page", "mixed_diagram", "mixed_logo", "scan_rot180", "scan_rotate_attr",
        "scan_two_columns", "mixed_diagram_rot90",
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

    diagram_png, logo_png = out / "diagram.png", out / "logo.png"
    text_page(DIAGRAM_LINES, size=44, px=(900, 400)).save(diagram_png)
    Image.new("RGB", (60, 60), "navy").save(logo_png)

    def with_picture(png: Path, w: float, h: float):
        def draw(c):
            _text_page_draw("Texto")(c)
            c.drawImage(str(png), 72, 100, width=w, height=h)
        return draw

    _reportlab_pdf(p["mixed_diagram"], [with_picture(diagram_png, 450, 200)])   # ~18 % de la página
    def rotated(draw):
        def d(c):
            c.setPageRotation(90)
            draw(c)
        return d

    _reportlab_pdf(p["mixed_diagram_rot90"], [rotated(with_picture(diagram_png, 450, 200))])
    _reportlab_pdf(p["mixed_logo"], [with_picture(logo_png, 40, 40)])           # ~0.3 %: decoración

    scan_pdf_images(p["scan_rot180"], [text_page(ES_LINES).rotate(180)])
    scan_pdf_images(p["scan_two_columns"], [two_column_page()])
    # /Rotate 90 con la imagen girada 90° a la izquierda: en pantalla queda derecha (pdfium debe respetar /Rotate).
    rotated_png = out / "es_rot.png"
    text_page(ES_LINES).rotate(90, expand=True).save(rotated_png)
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(p["scan_rotate_attr"]), pagesize=(A4[1], A4[0]))
    c.setPageRotation(90)
    c.drawImage(str(rotated_png), 0, 0, width=A4[1], height=A4[0])
    c.showPage()
    c.save()

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
