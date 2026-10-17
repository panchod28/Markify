import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from make_fixtures import make_fixtures


@pytest.fixture(scope="session")
def pdfs(tmp_path_factory) -> dict[str, Path]:
    return make_fixtures(tmp_path_factory.mktemp("pdfs"))
