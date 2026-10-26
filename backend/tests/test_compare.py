import pytest
import torch
from fastapi.testclient import TestClient

import main
from rl.dqn_agent import DQNAgent
from rl.env import env_signature

BODY = {"n_seeds": 2, "num_tasks": 40}


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def weights(tmp_path, monkeypatch):
    path = tmp_path / "dqn.pt"
    torch.save(DQNAgent(50, 16, seed=0).checkpoint({"env_signature": env_signature()}), path)
    monkeypatch.setenv("DCTWIN_DQN_WEIGHTS", str(path))


def test_compare_runs_every_policy_on_same_seeds(client, weights):
    resp = client.post("/api/compare", json=BODY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["policies"] == ["min-min", "power-aware", "dqn"]
    assert body["seeds"] == [1000, 1001]
    assert body["skipped"] == {}
    for policy in body["policies"]:
        for metric in ("total_energy_kwh", "makespan", "avg_utilization", "sla_violations"):
            assert set(body["summary"][policy][metric]) == {"mean", "std"}
    assert body["summary"]["min-min"]["vs_baseline_pct"]["total_energy_kwh"] == 0.0
    mm = body["summary"]["min-min"]["total_energy_kwh"]["mean"]
    pa = body["summary"]["power-aware"]["total_energy_kwh"]["mean"]
    assert body["summary"]["power-aware"]["vs_baseline_pct"]["total_energy_kwh"] == pytest.approx(100 * (mm - pa) / mm)


def test_latest_is_rebuilt_from_sqlite(client, weights):
    posted = client.post("/api/compare", json=BODY).json()
    latest = client.get("/api/compare/latest").json()
    assert latest["comparison_id"] == posted["comparison_id"]
    assert latest["summary"] == posted["summary"]
    assert client.get("/api/simulations/latest").status_code == 404  # comparison runs are not single runs


def test_dqn_skipped_without_weights(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DCTWIN_DQN_WEIGHTS", str(tmp_path / "missing.pt"))
    body = client.post("/api/compare", json=BODY).json()
    assert body["policies"] == ["min-min", "power-aware"]
    assert "train_dqn.py" in body["skipped"]["dqn"]


def test_training_seeds_rejected(client):
    assert client.post("/api/compare", json={**BODY, "seed_start": 0}).status_code == 422


def test_latest_404_before_any_comparison(client):
    assert client.get("/api/compare/latest").status_code == 404
