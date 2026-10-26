import pytest
import torch
from fastapi.testclient import TestClient

import main
import policies
from database import INITIAL_16_SERVERS
from rl.dqn_agent import DQNAgent
from rl.env import env_signature
from simulation import run_simulation


def _write_weights(path, signature):
    agent = DQNAgent(50, 16, seed=0)
    torch.save(agent.checkpoint({"env_signature": signature}), path)


def test_missing_weights_is_clear_503(tmp_path, monkeypatch):
    monkeypatch.setenv("DCTWIN_DQN_WEIGHTS", str(tmp_path / "nope.pt"))
    with pytest.raises(policies.PolicyUnavailable, match="train_dqn.py"):
        policies.get_policy("dqn")
    with TestClient(main.app) as client:
        resp = client.post("/api/simulations", json={"policy": "dqn"})
    assert resp.status_code == 503
    assert "train_dqn.py" in resp.json()["detail"]


def test_weights_for_other_config_are_rejected(tmp_path, monkeypatch):
    path = tmp_path / "dqn.pt"
    _write_weights(path, "stale-signature")
    monkeypatch.setenv("DCTWIN_DQN_WEIGHTS", str(path))
    with pytest.raises(policies.PolicyUnavailable, match="different engine configuration"):
        policies.get_policy("dqn")


def test_request_never_trains(tmp_path, monkeypatch):
    path = tmp_path / "dqn.pt"
    _write_weights(path, env_signature())
    monkeypatch.setenv("DCTWIN_DQN_WEIGHTS", str(path))

    def forbidden(*args, **kwargs):
        raise AssertionError("training code must not run during a request")

    monkeypatch.setattr(DQNAgent, "learn", forbidden)
    monkeypatch.setattr(DQNAgent, "remember", forbidden)
    policy = policies.get_policy("dqn")
    result = run_simulation(INITIAL_16_SERVERS, policy, num_tasks=40, seed=1000)
    again = run_simulation(INITIAL_16_SERVERS, policies.get_policy("dqn"), num_tasks=40, seed=1000)
    assert result == again
