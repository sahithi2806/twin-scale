import pytest

from database import INITIAL_16_SERVERS
from policies import POLICY_NAMES, MinMinPolicy, PowerAwarePolicy, get_policy
from simulation import run_simulation


def test_registry_lists_all_three():
    assert POLICY_NAMES == ("min-min", "power-aware", "dqn")
    assert isinstance(get_policy("power-aware"), PowerAwarePolicy)
    with pytest.raises(ValueError):
        get_policy("banana")


def test_power_aware_consolidates_and_saves_energy():
    mm = run_simulation(INITIAL_16_SERVERS, MinMinPolicy(), num_tasks=200, seed=1000)
    pa = run_simulation(INITIAL_16_SERVERS, PowerAwarePolicy(), num_tasks=200, seed=1000)
    used = lambda r: sum(s["tasks_assigned"] > 0 for s in r["server_stats"])  # noqa: E731
    assert used(pa) < used(mm)
    assert pa["total_energy_kwh"] < mm["total_energy_kwh"]
    assert pa["avg_utilization"] > mm["avg_utilization"]


def test_power_aware_is_deterministic():
    a = run_simulation(INITIAL_16_SERVERS, PowerAwarePolicy(), num_tasks=120, seed=1001)
    b = run_simulation(INITIAL_16_SERVERS, PowerAwarePolicy(), num_tasks=120, seed=1001)
    assert a == b
