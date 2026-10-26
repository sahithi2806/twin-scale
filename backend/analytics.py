"""Analytics over persisted runs. Everything here reads from SQLite, never from in-memory engine objects."""
import statistics
from typing import Any, Dict, List, Optional

import database
from config import IDLE_FLAG_FRACTION, OVERLOAD_FLAG_FRACTION
from evaluation import METRICS, summarize
from policies import POLICY_NAMES

BASELINE = "min-min"


def _flags_for(stat: Dict[str, Any]) -> List[str]:
    flags = []
    if stat["sleep_fraction"] + stat["idle_fraction"] > IDLE_FLAG_FRACTION:
        flags.append("idle")
    if stat["overload_fraction"] > OVERLOAD_FLAG_FRACTION:
        flags.append("overloaded")
    return flags


def flag_servers(run_id: str) -> Optional[List[Dict[str, Any]]]:
    """Idle: asleep or awake-with-no-work for > IDLE_FLAG_FRACTION of the run.
    Overloaded: above OVERLOAD_THRESHOLD utilization for > OVERLOAD_FLAG_FRACTION of the run."""
    run = database.get_run(run_id)
    if run is None:
        return None
    return [{
        "server_id": s["server_id"],
        "flags": _flags_for(s),
        "avg_utilization": s["avg_utilization"],
        "sleep_fraction": s["sleep_fraction"],
        "idle_fraction": s["idle_fraction"],
        "overload_fraction": s["overload_fraction"],
    } for s in run["server_stats"]]


def run_analytics(run_id: str) -> Optional[Dict[str, Any]]:
    servers = flag_servers(run_id)
    if servers is None:
        return None
    return {
        "server_flags": servers,
        "idle_servers": [s["server_id"] for s in servers if "idle" in s["flags"]],
        "overloaded_servers": [s["server_id"] for s in servers if "overloaded" in s["flags"]],
    }


def _mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def comparison_summary(comparison_id: str) -> Optional[Dict[str, Any]]:
    runs = database.get_comparison_runs(comparison_id)
    if not runs:
        return None
    by_policy: Dict[str, List[Dict[str, Any]]] = {}
    for run in sorted(runs, key=lambda r: r["seed"]):
        by_policy.setdefault(run["policy"], []).append(run)
    policies = [p for p in POLICY_NAMES if p in by_policy]
    by_policy = {p: by_policy[p] for p in policies}
    seeds = sorted({r["seed"] for r in runs})
    first = runs[0]

    summary = summarize(by_policy, baseline=BASELINE)

    per_server: Dict[str, List[Dict[str, Any]]] = {}
    server_flags: Dict[str, Dict[str, Any]] = {}
    for policy, policy_runs in by_policy.items():
        stats_by_server: Dict[str, List[Dict[str, Any]]] = {}
        idle_counts, overload_counts = [], []
        for run in policy_runs:
            flagged = [_flags_for(s) for s in run["server_stats"]]
            idle_counts.append(sum("idle" in f for f in flagged))
            overload_counts.append(sum("overloaded" in f for f in flagged))
            for s in run["server_stats"]:
                stats_by_server.setdefault(s["server_id"], []).append(s)
        per_server[policy] = [{
            "server_id": sid,
            "energy_kwh": _mean([s["energy_kwh"] for s in rows]),
            "avg_utilization": _mean([s["avg_utilization"] for s in rows]),
            "sleep_fraction": _mean([s["sleep_fraction"] for s in rows]),
            "tasks_assigned": _mean([s["tasks_assigned"] for s in rows]),
            "idle_in_runs": sum("idle" in _flags_for(s) for s in rows),
            "overloaded_in_runs": sum("overloaded" in _flags_for(s) for s in rows),
        } for sid, rows in sorted(stats_by_server.items())]
        server_flags[policy] = {"mean_idle_servers": _mean(idle_counts),
                                "mean_overloaded_servers": _mean(overload_counts)}

    base_sla = summary[BASELINE]["sla_violations"]["mean"] if BASELINE in summary else None
    sla_impact = {
        p: {
            "mean_violations": summary[p]["sla_violations"]["mean"],
            "violation_rate_pct": 100.0 * summary[p]["sla_violations"]["mean"] / max(1, first["num_tasks"]),
            "delta_vs_baseline": None if base_sla is None else summary[p]["sla_violations"]["mean"] - base_sla,
        } for p in policies
    }

    return {
        "comparison_id": comparison_id,
        "created_at": min(r["created_at"] for r in runs),
        "params": {k: first["parameters"][k] for k in ("num_tasks", "sleep_enabled", "sla_slack", "arrival_rate")},
        "seeds": seeds,
        "policies": policies,
        "skipped": {p: "not run in this comparison (DQN weights were unavailable)" for p in POLICY_NAMES
                    if p not in by_policy},
        "metrics": list(METRICS),
        "summary": summary,
        "per_server": per_server,
        "server_flags": server_flags,
        "sla_impact": sla_impact,
        "energy_saving": energy_saving(summary, per_server, sla_impact, "dqn"),
    }


def energy_saving(summary, per_server, sla_impact, policy: str) -> Optional[Dict[str, Any]]:
    """`policy` vs Min-Min: absolute and % energy saving, per-server breakdown, and the SLA cost of the saving."""
    if policy not in summary or BASELINE not in summary:
        return None
    base_kwh = summary[BASELINE]["total_energy_kwh"]["mean"]
    pol_kwh = summary[policy]["total_energy_kwh"]["mean"]
    base_servers = {s["server_id"]: s for s in per_server[BASELINE]}
    return {
        "policy": policy,
        "baseline": BASELINE,
        "baseline_kwh": base_kwh,
        "policy_kwh": pol_kwh,
        "saved_kwh": base_kwh - pol_kwh,
        "saved_pct": summary[policy]["vs_baseline_pct"]["total_energy_kwh"],
        "sla_violations_baseline": summary[BASELINE]["sla_violations"]["mean"],
        "sla_violations_policy": summary[policy]["sla_violations"]["mean"],
        "sla_cost": sla_impact[policy]["delta_vs_baseline"],
        "per_server": [{
            "server_id": s["server_id"],
            "baseline_kwh": base_servers[s["server_id"]]["energy_kwh"],
            "policy_kwh": s["energy_kwh"],
            "saved_kwh": base_servers[s["server_id"]]["energy_kwh"] - s["energy_kwh"],
            "policy_sleep_fraction": s["sleep_fraction"],
        } for s in per_server[policy]],
    }
