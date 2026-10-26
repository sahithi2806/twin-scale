"""Multi-seed evaluation on held-out seeds, shared by train_dqn.py --eval and POST /api/compare."""
import statistics
from typing import Any, Dict, List

EVAL_SEED_START = 1000
METRICS = ("total_energy_kwh", "makespan", "avg_utilization", "sla_violations")


def eval_seeds(n_seeds: int, seed_start: int = EVAL_SEED_START) -> List[int]:
    if seed_start < EVAL_SEED_START:
        raise ValueError(f"evaluation seeds must be >= {EVAL_SEED_START} (0-999 are reserved for training)")
    return list(range(seed_start, seed_start + n_seeds))


def mean_std(values: List[float]) -> Dict[str, float]:
    return {"mean": statistics.fmean(values), "std": statistics.stdev(values) if len(values) > 1 else 0.0}


def summarize(runs_by_policy: Dict[str, List[Dict[str, Any]]], baseline: str = "min-min") -> Dict[str, Any]:
    """runs_by_policy: policy -> list of per-seed run summaries (same seeds, same order)."""
    summary = {
        policy: {metric: mean_std([float(r[metric]) for r in runs]) for metric in METRICS}
        for policy, runs in runs_by_policy.items()
    }
    base = summary.get(baseline)
    for policy, stats in summary.items():
        savings = {}
        if base is not None:
            for metric in METRICS:
                b = base[metric]["mean"]
                savings[metric] = 100.0 * (b - stats[metric]["mean"]) / b if b else None
        stats["vs_baseline_pct"] = savings
    return summary


def format_table(summary: Dict[str, Any]) -> str:
    header = f"{'policy':<12} {'energy kWh':>18} {'makespan s':>16} {'util %':>14} {'SLA viol.':>14} {'energy vs MM':>13}"
    lines = [header, "-" * len(header)]
    for policy, s in summary.items():
        def cell(metric, fmt):
            return f"{s[metric]['mean']:{fmt}} ± {s[metric]['std']:{fmt}}"
        saving = s["vs_baseline_pct"].get("total_energy_kwh")
        lines.append(f"{policy:<12} {cell('total_energy_kwh', '.4f'):>18} {cell('makespan', '.1f'):>16} "
                     f"{cell('avg_utilization', '.1f'):>14} {cell('sla_violations', '.1f'):>14} "
                     f"{'' if saving is None else f'{saving:+.1f}%':>13}")
    return "\n".join(lines)
