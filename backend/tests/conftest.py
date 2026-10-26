import pytest

import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DCTWIN_DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    yield
