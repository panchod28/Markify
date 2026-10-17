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
    columns, spanning = _split_columns(kept, med_h)
    paragraphs: list[str] = []
    if len(columns) > 1 and spanning:  # título/pie que cruza las columnas: antes o después de ellas, no en medio
        content_top = min(l.box[1] for c in columns for l in c)
        before = [l for l in spanning if (l.box[1] + l.box[3]) / 2 < content_top]
        paragraphs.extend(_paragraphs(before, med_h) if before else [])
        spanning = [l for l in spanning if l not in before]
    for column in columns:
        paragraphs.extend(_paragraphs(column, med_h))
    if spanning:
        paragraphs.extend(_paragraphs(spanning, med_h))
    return "\n\n".join(paragraphs), dropped


def _split_columns(lines: list[OcrLine], med_h: float) -> tuple[list[list[OcrLine]], list[OcrLine]]:
    """(columnas, líneas que cruzan el hueco entre ellas). Columnas por huecos verticales libres en la
    proyección horizontal; primero sin tolerancia y luego tolerando unas pocas líneas puente (título, encabezado o pie centrado).
    Si no hay, una sola columna."""
    left = min(l.box[0] for l in lines)
    right = max(l.box[2] for l in lines)
    min_gap = max(1.0 * med_h, COLUMN_GAP_MIN * (right - left))  # las cajas del detector vienen infladas ~1.6x: un medianil de 24 pt llega como ~40 px
    for tolerance in (0, 2, max(3, len(lines) // 20)):  # hasta ~5 % de líneas puente (título, pie, encabezado)
        found = _columns(lines, min_gap, tolerance)
        if found:
            return found
    return [lines], []


def _columns(lines: list[OcrLine], min_gap: float, tolerance: int):
    xs = sorted({x for l in lines for x in (l.box[0], l.box[2])})
    gaps: list[list[float]] = []
    for x0, x1 in zip(xs, xs[1:]):
        covered = sum(1 for l in lines if l.box[0] < x1 and l.box[2] > x0)
        if covered <= tolerance:
            if gaps and gaps[-1][1] == x0:
                gaps[-1][1] = x1
            else:
                gaps.append([x0, x1])
    # Un hueco cuenta si mide lo suficiente y hay texto a ambos lados (no es el margen).
    gaps = [g for g in gaps if g[1] - g[0] >= min_gap
            and any(l.box[2] <= g[0] for l in lines) and any(l.box[0] >= g[1] for l in lines)]
    if not gaps:
        return None
    columns: list[list[OcrLine]] = [[] for _ in range(len(gaps) + 1)]
    spanning: list[OcrLine] = []
    for l in lines:
        if any(l.box[0] <= g[0] and l.box[2] >= g[1] or g[0] <= (l.box[0] + l.box[2]) / 2 <= g[1] for g in gaps):
            # cruza el hueco o está centrada en él (título, pie); si solo lo invade desde un lado, va por su centro
            spanning.append(l)
        else:
            cx = (l.box[0] + l.box[2]) / 2
            columns[sum(1 for g in gaps if cx > g[1])].append(l)
    # Una "columna" con una sola línea suele ser ruido (p. ej. un número de página): no partir el texto.
    if any(len(c) < 2 for c in columns):
        return None
    return columns, spanning


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
