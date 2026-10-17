import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from make_fixtures import make_fixtures


@pytest.fixture(scope="session")
def pdfs(tmp_path_factory) -> dict[str, Path]:
    return make_fixtures(tmp_path_factory.mktemp("pdfs"))


@pytest.fixture(scope="session")
def docx_files(tmp_path_factory) -> dict[str, Path]:
    from make_office_fixtures import make_docx_corpus
    return make_docx_corpus(tmp_path_factory.mktemp("docx"))


@pytest.fixture(scope="session")
def pptx_files(tmp_path_factory) -> dict[str, Path]:
    from make_office_fixtures import make_pptx_corpus
    return make_pptx_corpus(tmp_path_factory.mktemp("pptx"))
