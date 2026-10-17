import json
import queue
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import dispatcher

TIMEOUT = 5


class Harness:
    """Ejecuta dispatcher.run en un hilo con stdin simulado y handlers falsos."""

    def __init__(self, handlers, model_available=lambda: True):
        self.stdin = queue.Queue()
        self.out = []
        self.cancel_flag = threading.Event()
        self.thread = threading.Thread(
            target=dispatcher.run,
            kwargs=dict(
                handlers=handlers,
                cancel_flag=self.cancel_flag,
                model_available=model_available,
                read=self._read,
                write=self.out.append,
            ),
            daemon=True,
        )
        self.thread.start()

    def _read(self):
        item = self.stdin.get()
        if item is None:
            raise EOFError
        if isinstance(item, Exception):
            raise item
        return item

    def send(self, **msg):
        self.stdin.put(msg)

    def eof(self):
        self.stdin.put(None)
        self.thread.join(TIMEOUT)
        assert not self.thread.is_alive(), "run() no terminó tras EOF"


def wait_for(cond, what):
    deadline = threading.Event()
    for _ in range(int(TIMEOUT / 0.01)):
        if cond():
            return
        deadline.wait(0.01)
    raise AssertionError(f"timeout esperando: {what}")


def test_cancel_is_applied_while_convert_is_running():
    started, release = threading.Event(), threading.Event()

    def convert(_payload):
        started.set()
        release.wait(TIMEOUT)

    h = Harness({"convert": convert})
    h.send(command="convert", payload={})
    assert started.wait(TIMEOUT)
    h.send(command="cancel")
    wait_for(h.cancel_flag.is_set, "flag de cancelación activo con el trabajador ocupado")
    release.set()
    h.eof()


def test_check_model_answers_with_request_id_while_convert_is_running():
    started, release = threading.Event(), threading.Event()

    def convert(_payload):
        started.set()
        release.wait(TIMEOUT)

    h = Harness({"convert": convert}, model_available=lambda: True)
    h.send(command="convert", payload={})
    assert started.wait(TIMEOUT)
    h.send(id="abc", command="check_model", payload={})
    wait_for(lambda: len(h.out) == 1, "respuesta de check_model")
    assert h.out[0] == {"type": "model_status", "request_id": "abc", "payload": {"available": True}}
    assert not release.is_set()  # el convert seguía bloqueado
    release.set()
    h.eof()


def test_check_model_without_id_has_null_request_id():
    h = Harness({}, model_available=lambda: False)
    h.send(command="check_model", payload={})
    wait_for(lambda: len(h.out) == 1, "respuesta de check_model")
    assert h.out[0]["request_id"] is None
    assert h.out[0]["payload"] == {"available": False}
    h.eof()


def test_cancel_after_enqueue_is_kept_when_worker_has_not_started_the_job():
    first_started, release_first = threading.Event(), threading.Event()
    seen = []

    def convert(payload):
        if payload["n"] == 1:
            first_started.set()
            release_first.wait(TIMEOUT)
        else:
            seen.append(h.cancel_flag.is_set())

    h = Harness({"convert": convert})
    h.send(command="convert", payload={"n": 1})
    assert first_started.wait(TIMEOUT)
    h.send(command="convert", payload={"n": 2})  # encolado, el trabajador sigue con el 1
    h.send(command="cancel")
    wait_for(h.cancel_flag.is_set, "cancel procesado")
    release_first.set()
    h.eof()
    assert seen == [True]


def test_idle_cancel_does_not_affect_a_later_convert():
    seen = []
    h = Harness({"convert": lambda _p: seen.append(h.cancel_flag.is_set())})
    h.send(command="cancel")
    wait_for(h.cancel_flag.is_set, "cancel ocioso procesado")
    h.send(command="convert", payload={})
    h.eof()
    assert seen == [False]


def test_jobs_run_in_order_and_eof_drains_the_queue():
    order = []
    h = Harness({
        "convert": lambda p: order.append(("convert", p["n"])),
        "download_model": lambda _p: order.append(("download", None)),
    })
    h.send(command="convert", payload={"n": 1})
    h.send(command="download_model")
    h.send(command="convert", payload={"n": 2})
    h.eof()
    assert order == [("convert", 1), ("download", None), ("convert", 2)]


def test_errors_do_not_kill_reader_or_worker(capsys):
    calls = []

    def convert(payload):
        calls.append(payload["n"])
        if payload["n"] == 1:
            raise RuntimeError("boom")

    def model_available():
        raise OSError("disco")

    h = Harness({"convert": convert}, model_available=model_available)
    h.send(command="check_model", payload={})          # el handler del lector falla
    h.stdin.put(json.JSONDecodeError("mal", "x", 0))    # JSON inválido
    h.send(command="nope")                              # comando desconocido
    h.send(command="convert")                           # sin payload -> KeyError
    h.send(command="convert", payload={"n": 1})         # el handler lanza
    h.send(command="convert", payload={"n": 2})         # sigue funcionando
    h.send(command="cancel")
    wait_for(h.cancel_flag.is_set, "cancel tras errores")
    h.eof()
    assert calls == [1, 2]
    assert h.out == []                                  # nada a stdout salvo mensajes de protocolo
    err = capsys.readouterr().err
    assert "Comando desconocido: nope" in err and "boom" in err
