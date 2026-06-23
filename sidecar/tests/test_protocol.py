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
