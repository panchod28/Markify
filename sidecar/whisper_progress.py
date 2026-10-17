# sidecar/whisper_progress.py
"""
Progreso real y cancelación de la transcripción de Whisper.

`whisper.transcribe.transcribe` procesa el audio en ventanas de ~30 s dentro de
`with tqdm.tqdm(total=content_frames, ...) as pbar:` y llama a `pbar.update(n)` tras cada una.
Mientras dura la transcripción sustituimos ese `tqdm` por una barra mínima que, en cada
`update`, consulta el flag de cancelación y reporta el progreso.

Sin imports pesados (whisper/torch): el módulo de Whisper se recibe por parámetro, así se prueba con un falso.
"""

import sys
import threading
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Callable, Iterator


class TranscriptionCancelled(Exception):
    """El usuario canceló mientras Whisper transcribía."""


def _make_bar_class(cancel_flag: threading.Event, on_progress: Callable[[int], None]):
    class _Bar:
        def __init__(self, total=None, **_kwargs):
            self.total = total or 0
            self.done = 0
            self.last = 0

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def update(self, n=1):
            self.done += n
            if cancel_flag.is_set():
                raise TranscriptionCancelled()
            if self.total:
                # El 100 % lo marca el file_result, no la barra.
                pct = min(99, int(100 * self.done / self.total))
                if pct > self.last:
                    self.last = pct
                    on_progress(pct)

    return _Bar


@contextmanager
def hook_progress(
    whisper_transcribe_module,
    cancel_flag: threading.Event,
    on_progress: Callable[[int], None],
) -> Iterator[bool]:
    """
    Aplica el enganche durante el bloque y lo restaura siempre. Entrega True si se aplicó.
    Si esta versión de Whisper no expone `tqdm`, avisa por stderr y entrega False (sin cancelación
    intermedia ni progreso real, igual que antes).
    """
    if not hasattr(whisper_transcribe_module, "tqdm"):
        print("[Sidecar] whisper hook no disponible: transcribe sin cancelación intermedia", file=sys.stderr)
        yield False
        return

    original = whisper_transcribe_module.tqdm
    whisper_transcribe_module.tqdm = SimpleNamespace(tqdm=_make_bar_class(cancel_flag, on_progress))
    try:
        yield True
    finally:
        whisper_transcribe_module.tqdm = original
