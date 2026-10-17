import importlib
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from whisper_progress import TranscriptionCancelled, hook_progress


def fake_module():
    return SimpleNamespace(tqdm="original")


def run_windows(mod, flag, steps, total=100):
    """Simula el bucle de whisper.transcribe: with tqdm.tqdm(total=...) as pbar: pbar.update(n)."""
    events = []
    with hook_progress(mod, flag, events.append) as applied:
        assert applied
        with mod.tqdm.tqdm(total=total, unit="frames", disable=True) as pbar:
            for n in steps:
                pbar.update(n)
    return events


def test_progress_is_monotonic_integer_and_capped_at_99():
    events = run_windows(fake_module(), threading.Event(), [25, 25, 25, 25])
    assert events == [25, 50, 75, 99]


def test_progress_only_when_integer_changes():
    # 3 actualizaciones de 1 sobre 1000 no cambian el entero (0 %): no se emite nada
    assert run_windows(fake_module(), threading.Event(), [1, 1, 1], total=1000) == []
    # 12 de 1000 cruzan el 1 %: un solo valor
    assert run_windows(fake_module(), threading.Event(), [4, 4, 4], total=1000) == [1]


def test_single_window_emits_at_most_one_intermediate_value():
    assert run_windows(fake_module(), threading.Event(), [100]) == [99]


def test_cancel_raises_on_next_update():
    mod, flag, events = fake_module(), threading.Event(), []
    with pytest.raises(TranscriptionCancelled):
        with hook_progress(mod, flag, events.append):
            with mod.tqdm.tqdm(total=100) as pbar:
                pbar.update(25)
                flag.set()
                pbar.update(25)
    assert events == [25]


def test_hook_is_restored_even_on_cancel_or_error():
    mod, flag = fake_module(), threading.Event()
    flag.set()
    with pytest.raises(TranscriptionCancelled):
        with hook_progress(mod, flag, lambda p: None):
            with mod.tqdm.tqdm(total=10) as pbar:
                pbar.update(1)
    assert mod.tqdm == "original"

    with pytest.raises(RuntimeError):
        with hook_progress(mod, threading.Event(), lambda p: None):
            raise RuntimeError("boom")
    assert mod.tqdm == "original"


def test_missing_tqdm_degrades_with_warning(capsys):
    mod = SimpleNamespace()  # versión de whisper sin `tqdm`
    with hook_progress(mod, threading.Event(), lambda p: None) as applied:
        assert applied is False
    assert "whisper hook no disponible" in capsys.readouterr().err


def test_installed_whisper_exposes_the_hook_point():
    """Alarma: falla si una versión de Whisper cambia el punto de enganche."""
    pytest.importorskip("whisper")
    mod = importlib.import_module("whisper.transcribe")
    assert hasattr(mod.tqdm, "tqdm")


def test_transcribe_audio_cancels_and_reports_progress(tmp_path, monkeypatch, capsys):
    """transcribe_audio con un Whisper falso: progreso por ventana, cancelación y stdout solo JSON."""
    pytest.importorskip("whisper")
    import json
    import whisper_handler

    audio = tmp_path / "a.wav"
    audio.write_bytes(b"x")
    flag = threading.Event()
    mod = fake_module()

    class FakeModel:
        def transcribe(self, path, verbose, language, fp16):
            assert verbose is None  # con False Whisper imprime "Detected language" en stdout
            with mod.tqdm.tqdm(total=100) as pbar:
                for i in range(4):
                    if i == 2:
                        flag.set()  # el usuario cancela tras dos ventanas
                    pbar.update(25)
            return {"text": "no debería llegar"}

    monkeypatch.setattr(whisper_handler, "get_model_path", lambda: tmp_path)
    monkeypatch.setattr(whisper_handler.whisper, "load_model", lambda *a, **k: FakeModel())
    monkeypatch.setattr(whisper_handler, "_transcribe_module", lambda: mod)

    result = whisper_handler.transcribe_audio(str(audio), "f1", flag)

    assert result == ""
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines()]  # todas JSON válido
    assert [m["payload"]["progress"] for m in lines] == [25, 50]
    assert mod.tqdm == "original"
