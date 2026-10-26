from fastapi.testclient import TestClient

import main


def test_post_returns_run_id_then_completes():
    with TestClient(main.app) as client:
        resp = client.post("/api/simulations", json={"policy": "min-min", "num_tasks": 30, "seed": 3})
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "queued"
        run_id = body["run_id"]

        run = client.get(f"/api/simulations/{run_id}").json()
        assert run["status"] == "done"
        assert run["progress"] == 1.0
        assert run["total_energy_kwh"] > 0
        assert run["server_stats"] and all(s["run_id"] == run_id for s in run["server_stats"])
        assert run["step_metrics"] and all(m["run_id"] == run_id for m in run["step_metrics"])


def test_run_is_queued_before_worker_starts(monkeypatch):
    seen = {}

    def spy(run_id, *args, **kwargs):
        seen["status"] = main.get_run(run_id, details=False)["status"]

    monkeypatch.setattr(main, "execute_run", spy)
    with TestClient(main.app) as client:
        resp = client.post("/api/simulations", json={"policy": "min-min", "num_tasks": 30, "seed": 3})
        assert resp.status_code == 202
    assert seen["status"] == "queued"


def test_engine_error_marks_run_failed(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(main, "run_engine", boom)
    with TestClient(main.app) as client:
        run_id = client.post("/api/simulations", json={"policy": "min-min", "num_tasks": 30}).json()["run_id"]
        run = client.get(f"/api/simulations/{run_id}").json()
    assert run["status"] == "failed"
    assert "engine exploded" in run["error"]


def test_unknown_run_is_404():
    with TestClient(main.app) as client:
        assert client.get("/api/simulations/RUN-DOESNOTEXIST").status_code == 404
