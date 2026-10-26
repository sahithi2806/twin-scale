from fastapi.testclient import TestClient

import config
import main


def test_deadline_formula():
    # 50,000 MI on 2 vCPUs at 2,500 MIPS/core -> 10 s ideal runtime
    assert config.ideal_exec_time(50_000, 2) == 10.0
    assert config.task_deadline(5.0, 50_000, 2, slack=1.5) == 20.0
    assert config.task_deadline(5.0, 50_000, 2) == 5.0 + config.SLA_DEADLINE_SLACK * 10.0


def test_violation_is_finishing_after_deadline():
    assert not config.is_sla_violation(20.0, 20.0)
    assert config.is_sla_violation(20.01, 20.0)


def test_slack_is_configurable_per_request():
    with TestClient(main.app) as client:
        def violations(slack):
            run_id = client.post("/api/simulations", json={
                "policy": "min-min", "num_tasks": 80, "seed": 5, "sla_slack": slack}).json()["run_id"]
            run = client.get(f"/api/simulations/{run_id}").json()
            assert run["sla_slack"] == slack
            return run["sla_violations"]

        assert violations(1.0) >= violations(5.0)
        assert client.post("/api/simulations", json={"sla_slack": 0.5}).status_code == 422
