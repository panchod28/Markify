# sidecar/ocr/layout.py
"""
Líneas OCR -> texto Markdown legible: filtra por confianza, ordena en lectura (columnas, filas) y une
líneas en párrafos. Función pura, sin OCR ni I/O. No infiere encabezados ni tablas (el OCR no los conoce).
"""

from statistics import median

from ocr.base import OcrLine

MIN_CONFIDENCE = 0.5      # por debajo, la línea se descarta (y se avisa con un conteo agregado)
ROW_OVERLAP = 0.5         # fracción de la altura mediana: misma fila si los centros difieren menos que esto
PARAGRAPH_GAP = 0.8       # hueco vertical (en alturas medianas) a partir del cual empieza otro párrafo
COLUMN_GAP_MIN = 0.03     # hueco horizontal mínimo entre columnas, como fracción del ancho del texto


def lines_to_markdown(lines: list[OcrLine], min_confidence: float = MIN_CONFIDENCE) -> tuple[str, int]:
    """Devuelve (texto, líneas descartadas por baja confianza)."""
    dropped = sum(1 for l in lines if l.confidence < min_confidence)
    kept = [l for l in lines if l.confidence >= min_confidence and l.text.strip()]
    if not kept:
        return "", dropped

    med_h = median(max(1.0, l.box[3] - l.box[1]) for l in kept)
    paragraphs: list[str] = []
    for column in _split_columns(kept, med_h):
        paragraphs.extend(_paragraphs(column, med_h))
    return "\n\n".join(paragraphs), dropped


def _split_columns(lines: list[OcrLine], med_h: float) -> list[list[OcrLine]]:
    """Columnas por huecos verticales libres en la proyección horizontal. Si no hay, una sola columna."""
    left = min(l.box[0] for l in lines)
    right = max(l.box[2] for l in lines)
    min_gap = max(1.5 * med_h, COLUMN_GAP_MIN * (right - left))

    # Fusionar los intervalos horizontales ocupados y mirar los huecos entre ellos.
    spans = sorted((l.box[0], l.box[2]) for l in lines)
    merged = [list(spans[0])]
    for x0, x1 in spans[1:]:
        if x0 - merged[-1][1] >= min_gap:
            merged.append([x0, x1])
        else:
            merged[-1][1] = max(merged[-1][1], x1)
    if len(merged) < 2:
        return [lines]

    columns: list[list[OcrLine]] = [[] for _ in merged]
    for l in lines:
        cx = (l.box[0] + l.box[2]) / 2
        idx = min(range(len(merged)), key=lambda i: 0 if merged[i][0] <= cx <= merged[i][1] else min(abs(cx - merged[i][0]), abs(cx - merged[i][1])))
        columns[idx].append(l)
    # Una "columna" con una sola línea suele ser ruido (p. ej. un número de página): no partir el texto.
    if any(len(c) < 2 for c in columns):
        return [lines]
    return columns


def _paragraphs(lines: list[OcrLine], med_h: float) -> list[str]:
    rows = _rows(lines, med_h)
    paragraphs: list[list[str]] = []
    prev_bottom = None
    for row in rows:
        top = min(l.box[1] for l in row)
        bottom = max(l.box[3] for l in row)
        text = " ".join(l.text.strip() for l in sorted(row, key=lambda l: l.box[0]))
        if prev_bottom is None or top - prev_bottom > PARAGRAPH_GAP * med_h:
            paragraphs.append([text])
        else:
            paragraphs[-1].append(text)
        prev_bottom = bottom
    return [" ".join(p) for p in paragraphs]


def _rows(lines: list[OcrLine], med_h: float) -> list[list[OcrLine]]:
    """Agrupa cajas que están en la misma fila visual (centros verticales cercanos)."""
    ordered = sorted(lines, key=lambda l: (l.box[1] + l.box[3]) / 2)
    rows: list[list[OcrLine]] = []
    for l in ordered:
        cy = (l.box[1] + l.box[3]) / 2
        if rows and abs(cy - _row_center(rows[-1])) < ROW_OVERLAP * med_h:
            rows[-1].append(l)
        else:
            rows.append([l])
    return rows


def _row_center(row: list[OcrLine]) -> float:
    return sum((l.box[1] + l.box[3]) / 2 for l in row) / len(row)
