import pytest

import analytics
import database


def _stat(server_id, sleep=0.0, idle=0.0, overload=0.0, energy=1.0):
    return {"server_id": server_id, "avg_utilization": 10.0, "energy_kwh": energy, "tasks_assigned": 1,
            "sleep_fraction": sleep, "idle_fraction": idle, "overload_fraction": overload, "flags": ""}


def _store(run_id, policy, seed, stats, violations=0, comparison_id=None):
    params = {"seed": seed, "num_tasks": 100, "sleep_enabled": True, "sla_slack": 1.5, "arrival_rate": 3.0}
    database.create_run(run_id, policy, params, comparison_id=comparison_id)
    database.save_run_results(run_id, {
        "makespan": 50.0, "total_energy_kwh": sum(s["energy_kwh"] for s in stats), "avg_utilization": 10.0,
        "sla_violations": violations, "server_stats": stats, "step_metrics": [], "servers": []}, update_servers=False)


def test_flags_idle_and_overloaded_from_sqlite():
    _store("RUN-F", "min-min", 1, [
        _stat("SRV-01", sleep=0.7, idle=0.2),      # 0.9 idle share -> idle
        _stat("SRV-02", sleep=0.5, idle=0.2),      # 0.7 -> not idle
        _stat("SRV-03", overload=0.3),             # overloaded
        _stat("SRV-04", overload=0.2),             # exactly at threshold -> not overloaded
    ])
    result = analytics.run_analytics("RUN-F")
    assert result["idle_servers"] == ["SRV-01"]
    assert result["overloaded_servers"] == ["SRV-03"]
    assert analytics.run_analytics("RUN-MISSING") is None


def test_comparison_energy_saving_and_sla_cost():
    for seed in (1000, 1001):
        _store(f"MM-{seed}", "min-min", seed, [_stat("SRV-01", energy=2.0), _stat("SRV-02", energy=2.0)],
               violations=0, comparison_id="CMP-T")
        _store(f"DQ-{seed}", "dqn", seed, [_stat("SRV-01", energy=2.0), _stat("SRV-02", sleep=0.9, energy=1.0)],
               violations=3, comparison_id="CMP-T")
    summary = analytics.comparison_summary("CMP-T")
    assert summary["policies"] == ["min-min", "dqn"]
    assert "power-aware" in summary["skipped"]
    saving = summary["energy_saving"]
    assert saving["saved_kwh"] == pytest.approx(1.0)
    assert saving["saved_pct"] == pytest.approx(25.0)
    assert saving["sla_cost"] == pytest.approx(3.0)
    by_server = {s["server_id"]: s for s in saving["per_server"]}
    assert by_server["SRV-02"]["saved_kwh"] == pytest.approx(1.0)
    assert by_server["SRV-01"]["saved_kwh"] == pytest.approx(0.0)
    assert summary["server_flags"]["dqn"]["mean_idle_servers"] == 1.0


def test_no_energy_saving_without_dqn():
    _store("MM-1", "min-min", 1000, [_stat("SRV-01")], comparison_id="CMP-N")
    assert analytics.comparison_summary("CMP-N")["energy_saving"] is None
    assert analytics.comparison_summary("CMP-NONE") is None
