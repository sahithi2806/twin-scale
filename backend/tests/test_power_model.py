import pytest

import config
from policies import MinMinPolicy
from simulation import DataCenter, Task, power_draw, run_simulation

ONE_SERVER = [{"server_id": "SRV-T", "capacity": "64 vCPU / 256 GB RAM", "rack_id": "R"}]
P_IDLE, P_MAX = config.POWER_CLASSES[64]


def _task(arrival, vcpus=8, exec_time=10.0):
    return Task(task_id="T1", workload_mi=exec_time * vcpus * config.MIPS_PER_CORE, vcpus=vcpus,
                arrival_time=arrival, exec_time=exec_time, deadline=arrival + 100.0)


def _run(dc: DataCenter, tasks):
    dc.load(tasks)
    while not dc.done():
        for t in dc.pop_arrivals():
            dc.assign(t, 0)
        dc.tick()
    return dc


@pytest.mark.parametrize("u, expected", [(0.0, P_IDLE), (0.5, P_IDLE + 0.5 * (P_MAX - P_IDLE)), (1.0, P_MAX)])
def test_linear_power_when_awake(u, expected):
    assert power_draw("on", u, P_IDLE, P_MAX) == pytest.approx(expected)


def test_utilization_is_clamped():
    assert power_draw("on", 1.7, P_IDLE, P_MAX) == pytest.approx(P_MAX)
    assert power_draw("on", -0.2, P_IDLE, P_MAX) == pytest.approx(P_IDLE)


def test_sleep_and_waking_power():
    assert power_draw("sleep", 0.0, P_IDLE, P_MAX) == config.P_SLEEP_W
    assert config.P_SLEEP_W < 0.2 * P_IDLE
    assert power_draw("waking", 0.0, P_IDLE, P_MAX) == P_IDLE


def test_energy_integrates_power_over_time():
    dc = _run(DataCenter(ONE_SERVER, sleep_enabled=False), [_task(0.0, vcpus=8, exec_time=10.0)])
    expected_j = 10 * (P_IDLE + (P_MAX - P_IDLE) * 8 / 64)
    assert dc.energy_j == pytest.approx(expected_j)
    assert dc.tasks[0].finish_time == pytest.approx(10.0)


def test_idle_server_sleeps_after_timeout():
    dc = DataCenter(ONE_SERVER, sleep_enabled=True)
    dc.load([_task(1000.0)])
    for _ in range(int(config.IDLE_TIMEOUT_S)):
        dc.tick()
    assert dc.servers[0].state == "sleep"


def test_wake_up_delay_postpones_start():
    arrival = 20.5
    dc = _run(DataCenter(ONE_SERVER, sleep_enabled=True), [_task(arrival)])
    dispatch_time = 21.0  # first tick boundary after arrival
    assert dc.tasks[0].start_time == pytest.approx(dispatch_time + config.WAKE_DELAY_S)
    asleep_s = dispatch_time - config.IDLE_TIMEOUT_S
    expected_j = (config.IDLE_TIMEOUT_S * P_IDLE + asleep_s * config.P_SLEEP_W
                  + config.WAKE_DELAY_S * P_IDLE + 10 * (P_IDLE + (P_MAX - P_IDLE) * 8 / 64))
    assert dc.energy_j == pytest.approx(expected_j)


def test_estimate_start_includes_wake_delay():
    dc = DataCenter(ONE_SERVER, sleep_enabled=True)
    server = dc.servers[0]
    server.state = "sleep"
    assert server.estimate_start(4, now=50.0) == pytest.approx(50.0 + config.WAKE_DELAY_S)


def test_sleep_toggle_changes_energy_not_work():
    servers = [{"server_id": f"S{i}", "capacity": "64 vCPU", "rack_id": "R"} for i in range(4)]
    on = run_simulation(servers, MinMinPolicy(), num_tasks=40, seed=7, sleep_enabled=True, arrival_rate=0.2)
    off = run_simulation(servers, MinMinPolicy(), num_tasks=40, seed=7, sleep_enabled=False, arrival_rate=0.2)
    assert on["total_energy_kwh"] < off["total_energy_kwh"]
    assert sum(s["sleep_fraction"] for s in off["server_stats"]) == 0
    assert sum(s["sleep_fraction"] for s in on["server_stats"]) > 0
