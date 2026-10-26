from fastapi.testclient import TestClient

import main
from database import INITIAL_16_SERVERS
from policies import MinMinPolicy
from simulation import generate_workload, run_simulation

METRIC_KEYS = ("makespan", "total_energy_kwh", "avg_utilization", "sla_violations")


def test_workload_generator_is_seeded():
    a = generate_workload(50, seed=11)
    b = generate_workload(50, seed=11)
    c = generate_workload(50, seed=12)
    assert a == b
    assert a != c


def test_engine_same_seed_same_policy_identical():
    a = run_simulation(INITIAL_16_SERVERS, MinMinPolicy(), num_tasks=150, seed=1001)
    b = run_simulation(INITIAL_16_SERVERS, MinMinPolicy(), num_tasks=150, seed=1001)
    assert a == b


def test_engine_different_seed_differs():
    a = run_simulation(INITIAL_16_SERVERS, MinMinPolicy(), num_tasks=150, seed=1001)
    b = run_simulation(INITIAL_16_SERVERS, MinMinPolicy(), num_tasks=150, seed=1002)
    assert a["total_energy_kwh"] != b["total_energy_kwh"]


def _strip(run):
    return (
        {k: run[k] for k in METRIC_KEYS},
        [{k: v for k, v in s.items() if k not in ("id", "run_id")} for s in run["server_stats"]],
        [{k: v for k, v in m.items() if k not in ("id", "run_id")} for m in run["step_metrics"]],
    )


def test_stored_metrics_identical_across_runs():
    with TestClient(main.app) as client:
        body = {"policy": "min-min", "num_tasks": 120, "seed": 1003}
        ids = [client.post("/api/simulations", json=body).json()["run_id"] for _ in range(2)]
        runs = [client.get(f"/api/simulations/{i}").json() for i in ids]
    assert ids[0] != ids[1]
    assert _strip(runs[0]) == _strip(runs[1])
