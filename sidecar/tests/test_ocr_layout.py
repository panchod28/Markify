import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr.base import OcrLine
from ocr.layout import lines_to_markdown


def line(text, x0, y0, x1=None, h=30, conf=0.99):
    return OcrLine(text, (x0, y0, x1 if x1 is not None else x0 + 10 * len(text), y0 + h), conf)


def test_lines_close_together_become_one_paragraph_and_gaps_split_paragraphs():
    lines = [line("Primera línea", 100, 100), line("sigue aquí.", 100, 140),
             line("Otro párrafo", 100, 240), line("termina.", 100, 280)]
    text, dropped = lines_to_markdown(lines)
    assert text == "Primera línea sigue aquí.\n\nOtro párrafo termina."
    assert dropped == 0


def test_reading_order_is_top_to_bottom_regardless_of_input_order():
    lines = [line("tres", 100, 180), line("uno", 100, 100), line("dos", 100, 140)]
    assert lines_to_markdown(lines)[0] == "uno dos tres"


def test_low_confidence_lines_are_dropped_and_counted():
    lines = [line("bueno", 100, 100), line("ruido", 100, 140, conf=0.3), line("otro", 100, 180, conf=0.49)]
    text, dropped = lines_to_markdown(lines)
    assert text == "bueno" and dropped == 2


def test_all_dropped_gives_empty_text():
    assert lines_to_markdown([line("x", 0, 0, conf=0.1)]) == ("", 1)
    assert lines_to_markdown([]) == ("", 0)


def test_two_columns_are_read_one_after_the_other():
    left = [line(f"izq{i}", 100, 100 + 40 * i, 400) for i in range(4)]
    right = [line(f"der{i}", 700, 100 + 40 * i, 1000) for i in range(4)]
    # entrelazadas, como las devuelve un OCR por filas
    mixed = [l for pair in zip(left, right) for l in pair]
    text, _ = lines_to_markdown(mixed)
    assert text == "izq0 izq1 izq2 izq3\n\nder0 der1 der2 der3"


def test_single_line_in_a_side_column_does_not_split_the_text():
    body = [line(f"cuerpo{i}", 100, 100 + 40 * i, 900) for i in range(4)]
    page_no = line("12", 1000, 100, 1030)  # ruido a un lado: no es una columna
    assert lines_to_markdown(body + [page_no])[0] == "cuerpo0 12 cuerpo1 cuerpo2 cuerpo3"


def test_boxes_in_the_same_row_are_joined_left_to_right():
    lines = [line("derecha", 300, 100, 400), line("izquierda", 100, 102, 200)]
    assert lines_to_markdown(lines)[0] == "izquierda derecha"


def test_whitespace_is_trimmed():
    assert lines_to_markdown([line("  hola  ", 0, 0)])[0] == "hola"


def test_dense_justified_columns_with_title_and_footer_read_column_by_column():
    # Medidas de una página real: cajas del detector de 33 px de alto, medianil de ~40 px y varias líneas
    # (título, encabezado, pie) que cruzan o tocan el hueco.
    lines = [line("TITULO", 270, 50, 950, h=33), line("encabezado", 100, 100, 1130, h=33)]
    for i in range(14):
        y = 160 + i * 40
        lines.append(line(f"izq {i}", 104, y, 590 + (10 if i % 5 == 0 else 0), h=33))
        lines.append(line(f"der {i}", 647 - (7 if i % 6 == 0 else 0), y, 1130, h=33))
    lines.append(line("Pagina 1", 560, 1650, 670, h=33))
    text, _ = lines_to_markdown(lines)
    order = ["TITULO", "encabezado", "izq 0", "izq 13", "der 0", "der 13", "Pagina 1"]
    assert [text.index(t) for t in order] == sorted(text.index(t) for t in order), text
    assert text.index("izq 7") < text.index("izq 8") < text.index("der 0")


def test_single_column_with_a_ragged_right_edge_is_not_split():
    lines = [line(f"línea {i} " + "x" * (i * 7 % 40), 100, 100 + i * 40, h=33) for i in range(20)]
    text, _ = lines_to_markdown(lines)
    assert [text.index(f"línea {i} ") for i in range(20)] == sorted(text.index(f"línea {i} ") for i in range(20))
