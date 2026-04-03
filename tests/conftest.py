import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    app = create_app(db_url)
    with TestClient(app) as c:
        yield c