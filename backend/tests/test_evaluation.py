import pytest

import train_dqn
from evaluation import EVAL_SEED_START, eval_seeds, summarize


def test_seed_sets_never_overlap():
    train, val = set(train_dqn.TRAIN_SEEDS), set(train_dqn.VALIDATION_SEEDS)
    held_out = set(eval_seeds(50))
    assert train == set(range(100))
    assert not train & val and not train & held_out and not val & held_out
    assert min(held_out) == EVAL_SEED_START == 1000


def test_eval_rejects_training_seeds():
    with pytest.raises(ValueError):
        eval_seeds(10, seed_start=5)


def test_summary_mean_std_and_savings():
    def run(e, m, u, v):
        return {"total_energy_kwh": e, "makespan": m, "avg_utilization": u, "sla_violations": v}

    summary = summarize({
        "min-min": [run(1.0, 10, 20, 0), run(3.0, 10, 20, 2)],
        "dqn": [run(1.0, 12, 40, 1), run(1.0, 12, 40, 3)],
    })
    assert summary["min-min"]["total_energy_kwh"] == pytest.approx({"mean": 2.0, "std": 2 ** 0.5})
    assert summary["dqn"]["vs_baseline_pct"]["total_energy_kwh"] == pytest.approx(50.0)
    assert summary["dqn"]["vs_baseline_pct"]["makespan"] == pytest.approx(-20.0)
    assert summary["min-min"]["vs_baseline_pct"]["total_energy_kwh"] == 0.0
