import json
import io
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from protocol import read_message, write_message


def test_write_message():
    """Verifica que write_message escribe JSON + newline y hace flush."""
    fake_stdout = io.StringIO()
    with patch("sys.stdout", fake_stdout):
        write_message({"type": "test", "payload": {}})
    output = fake_stdout.getvalue()
    assert output.endswith("\n")
    parsed = json.loads(output.strip())
    assert parsed["type"] == "test"


def test_read_message():
    """Verifica que read_message parsea JSON correctamente."""
    fake_input = '{"command": "convert", "payload": {}}\n'
    with patch("sys.stdin", io.StringIO(fake_input)):
        msg = read_message()
    assert msg["command"] == "convert"


def test_write_message_is_thread_safe():
    """Varios hilos escribiendo a la vez: cada línea es un JSON completo."""
    import threading

    fake_stdout = io.StringIO()
    n_threads, n_msgs = 8, 200

    def writer(tid):
        for i in range(n_msgs):
            write_message({"type": "t", "thread": tid, "i": i, "pad": "x" * 200})

    with patch("sys.stdout", fake_stdout):
        threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
        [t.start() for t in threads]
        [t.join() for t in threads]

    lines = fake_stdout.getvalue().splitlines()
    assert len(lines) == n_threads * n_msgs
    assert all(json.loads(line)["type"] == "t" for line in lines)
