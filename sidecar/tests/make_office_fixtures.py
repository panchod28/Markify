# sidecar/tests/make_office_fixtures.py
"""
Genera DOCX y PPTX pequeños con imágenes para las pruebas de OCR en documentos de Office. Sin dependencias nuevas:
el DOCX se escribe a mano (zip + XML) y el PPTX con python-pptx (ya viaja con markitdown).

Bloques de `build_docx`:
    ("p", texto)
    ("img", PNG_o_bytes, ancho_px, alto_px, alt, extensión)      # imagen en línea
    ("table", [[celda, ...], ...])                               # celda = str o ("img", ...)
"""

import io
import zipfile
from html import escape
from pathlib import Path

from PIL import Image

from make_fixtures import DIAGRAM_LINES, ES_LINES, text_page

W_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
CONTENT_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "emf": "image/x-emf",
                 "wmf": "image/x-wmf", "svg": "image/svg+xml"}
# Cabecera mínima de un EMF: Pillow lo identifica pero no puede decodificarlo fuera de Windows.
FAKE_EMF = (b"\x01\x00\x00\x00" + b"\x6c\x00\x00\x00" + b"\x00" * 32 + b" EMF" + b"\x00" * 64)


def png_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    b = io.BytesIO()
    img.save(b, fmt)
    return b.getvalue()


def img(data: bytes, w: int, h: int, alt: str = "", ext: str = "png"):
    return ("img", data, w, h, alt, ext)


def _drawing(rid: str, n: int, w: int, h: int, alt: str) -> str:
    emu_w, emu_h = w * 9525, h * 9525
    return (f'<w:r><w:drawing><wp:inline><wp:extent cx="{emu_w}" cy="{emu_h}"/>'
            f'<wp:docPr id="{n}" name="Imagen {n}" descr="{escape(alt, quote=True)}"/>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="{n}" name="i{n}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def build_docx(path: Path, blocks: list) -> Path:
    media: list[tuple[str, bytes]] = []   # (nombre dentro de word/media, bytes)
    exts: set[str] = set()

    def image_run(block) -> str:
        _, data, w, h, alt, ext = block
        exts.add(ext)
        name = f"image{len(media) + 1}.{ext}"
        media.append((name, data))
        return _drawing(f"rId{100 + len(media)}", len(media), w, h, alt)

    def para(content: str) -> str:
        return f"<w:p>{content}</w:p>"

    body = []
    for b in blocks:
        if b[0] == "p":
            body.append(para(f"<w:r><w:t>{escape(b[1])}</w:t></w:r>"))
        elif b[0] == "img":
            body.append(para(image_run(b)))
        elif b[0] == "table":
            rows = []
            for row in b[1]:
                cells = []
                for cell in row:
                    inner = para(image_run(cell)) if isinstance(cell, tuple) else para(f"<w:r><w:t>{escape(cell)}</w:t></w:r>")
                    cells.append(f"<w:tc>{inner}</w:tc>")
                rows.append(f"<w:tr>{''.join(cells)}</w:tr>")
            body.append(f"<w:tbl>{''.join(rows)}</w:tbl>")
    doc = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W_NS}><w:body>{"".join(body)}</w:body></w:document>'
    defaults = "".join(f'<Default Extension="{e}" ContentType="{CONTENT_TYPES[e]}"/>' for e in sorted(exts))
    ct = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          f'<Default Extension="xml" ContentType="application/xml"/>{defaults}'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    drels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             + "".join(f'<Relationship Id="rId{101 + i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{n}"/>'
                       for i, (n, _) in enumerate(media)) + "</Relationships>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/_rels/document.xml.rels", drels)
        for name, data in media:
            z.writestr(f"word/media/{name}", data)
    return path


def make_docx_corpus(out: Path) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    shot = png_bytes(text_page(ES_LINES, size=44, px=(900, 420)))
    diagram = png_bytes(text_page(DIAGRAM_LINES, size=44, px=(900, 400)))
    icon = png_bytes(Image.new("RGB", (48, 48), "navy"))
    logo = png_bytes(Image.new("RGB", (240, 70), "darkgreen"))
    page = png_bytes(text_page(ES_LINES, size=54))                       # página escaneada completa
    page_180 = png_bytes(text_page(ES_LINES, size=54).rotate(180))
    photo = png_bytes(Image.effect_noise((900, 600), 60).convert("RGB"))  # imagen sin texto
    docs = {
        "solo_texto": [("p", "Un documento sin imágenes."), ("p", "Segundo párrafo con ñandú.")],
        "captura_entre_parrafos": [("p", "Antes de la imagen."), img(shot, 600, 280, "Captura del sistema"), ("p", "Después de la imagen.")],
        "solo_imagen": [img(page, 620, 877)],
        "pagina_escaneada_180": [("p", "Escaneo girado:"), img(page_180, 620, 877)],
        "iconos_y_logo": [("p", "Texto."), img(icon, 32, 32), img(logo, 240, 70), img(icon, 32, 32)],
        "misma_imagen_repetida": [("p", "Uno"), img(shot, 600, 280), ("p", "Dos"), img(shot, 600, 280), ("p", "Tres"), img(shot, 600, 280)],
        "imagen_en_tabla": [("p", "Tabla:"), ("table", [["Celda A", img(diagram, 450, 200)], ["Celda C", "Celda D"]])],
        "alt_automatico": [img(shot, 600, 280, "image.png"), ("p", "x"), img(shot, 500, 233, "Imagen 3")],
        "foto_sin_texto": [("p", "Una foto:"), img(photo, 600, 400)],
        "emf_y_captura": [img(FAKE_EMF, 200, 100, "", "emf"), ("p", "Entre."), img(FAKE_EMF, 200, 100, "", "emf"), img(shot, 600, 280)],
        "imagen_corrupta": [("p", "Hola"), img(b"esto no es una imagen", 300, 200), ("p", "Fin")],
    }
    return {name: build_docx(out / f"{name}.docx", blocks) for name, blocks in docs.items()}
