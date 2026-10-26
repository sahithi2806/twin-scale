import database


def _fake_result(energy: float, servers=("SRV-01", "SRV-02")):
    return {
        "makespan": 10.0,
        "total_energy_kwh": energy,
        "avg_utilization": 50.0,
        "sla_violations": 1,
        "server_stats": [{
            "server_id": s, "avg_utilization": 50.0, "energy_kwh": energy / len(servers), "tasks_assigned": 3,
            "sleep_fraction": 0.0, "idle_fraction": 0.1, "overload_fraction": 0.0, "flags": "",
        } for s in servers],
        "step_metrics": [{
            "step": step, "timestamp": float(step), "server_id": s, "utilization": 50.0,
            "energy_kwh": energy / 10, "power_state": "on", "queue_len": 0,
        } for step in range(1, 4) for s in servers],
        "servers": [],
    }


def _params(seed):
    return {"seed": seed, "num_tasks": 10, "sleep_enabled": True, "sla_slack": 1.5}


def test_rows_are_isolated_per_run():
    database.create_run("RUN-A", "min-min", _params(1))
    database.create_run("RUN-B", "min-min", _params(2))
    database.save_run_results("RUN-A", _fake_result(1.0), update_servers=False)
    database.save_run_results("RUN-B", _fake_result(2.0, servers=("SRV-03",)), update_servers=False)

    a = database.get_run("RUN-A")
    b = database.get_run("RUN-B")

    assert {s["run_id"] for s in a["server_stats"]} == {"RUN-A"}
    assert {m["run_id"] for m in a["step_metrics"]} == {"RUN-A"}
    assert {s["server_id"] for s in a["server_stats"]} == {"SRV-01", "SRV-02"}
    assert len(a["step_metrics"]) == 6

    assert {s["server_id"] for s in b["server_stats"]} == {"SRV-03"}
    assert len(b["step_metrics"]) == 3
    assert a["total_energy_kwh"] == 1.0 and b["total_energy_kwh"] == 2.0


def test_delete_cascades_only_to_own_rows():
    database.create_run("RUN-A", "min-min", _params(1))
    database.create_run("RUN-B", "min-min", _params(2))
    database.save_run_results("RUN-A", _fake_result(1.0), update_servers=False)
    database.save_run_results("RUN-B", _fake_result(2.0), update_servers=False)

    database.delete_run("RUN-A")

    conn = database.get_db_connection()
    try:
        orphan_stats = conn.execute("SELECT COUNT(*) FROM server_stats WHERE run_id = 'RUN-A'").fetchone()[0]
        orphan_steps = conn.execute("SELECT COUNT(*) FROM step_metrics WHERE run_id = 'RUN-A'").fetchone()[0]
        kept = conn.execute("SELECT COUNT(*) FROM step_metrics WHERE run_id = 'RUN-B'").fetchone()[0]
    finally:
        conn.close()
    assert orphan_stats == 0 and orphan_steps == 0
    assert kept == 6


def test_child_rows_require_existing_run():
    conn = database.get_db_connection()
    try:
        try:
            with conn:
                conn.execute(
                    "INSERT INTO step_metrics (run_id, step, timestamp, server_id, utilization, energy_kwh, "
                    "power_state, queue_len) VALUES ('NOPE', 1, 0, 'SRV-01', 0, 0, 'on', 0)")
            raised = False
        except Exception:
            raised = True
    finally:
        conn.close()
    assert raised, "foreign keys must be enforced"


def test_failed_partial_write_leaves_no_rows():
    database.create_run("RUN-A", "min-min", _params(1))
    bad = _fake_result(1.0)
    del bad["step_metrics"][-1]["queue_len"]
    try:
        database.save_run_results("RUN-A", bad, update_servers=False)
    except KeyError:
        pass
    run = database.get_run("RUN-A")
    assert run["status"] == "queued"
    assert run["server_stats"] == [] and run["step_metrics"] == []
