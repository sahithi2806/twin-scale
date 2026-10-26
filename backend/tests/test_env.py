import numpy as np
import pytest

import config
from database import INITIAL_16_SERVERS
from policies import Policy
from rl.env import DataCenterEnv, observation_size
from simulation import run_simulation


class RoundRobin(Policy):
    def __init__(self):
        self.next = 0

    def select(self, dc, task):
        idx = self.next % len(dc.servers)
        self.next += 1
        return idx


def _play(env, seed, actions=None):
    obs = env.reset(seed)
    env.energy_at_reset_j = env.dc.energy_j
    total, steps, done, info_sum = 0.0, 0, False, {"energy_wh": 0.0, "sla_violations": 0, "overload": 0.0}
    while not done:
        action = actions(steps) if actions else steps % env.n_actions
        obs, reward, done, info = env.step(action)
        total += reward
        steps += 1
        for k in info_sum:
            info_sum[k] += info[k]
    return obs, total, steps, info_sum


def test_reset_returns_observation_of_expected_shape():
    env = DataCenterEnv(num_tasks=30)
    obs = env.reset(seed=0)
    assert obs.shape == (observation_size(16),) == (50,)
    assert obs.dtype == np.float32
    assert 0.0 < obs[-2] <= 1.0  # next task vCPU demand is present


def test_reset_is_deterministic_and_restarts():
    env = DataCenterEnv(num_tasks=30)
    first = env.reset(seed=4)
    _play(env, seed=4)
    again = env.reset(seed=4)
    np.testing.assert_array_equal(first, again)
    assert env.dc.completed == 0


def test_episode_has_one_step_per_task_and_terminates():
    env = DataCenterEnv(num_tasks=40)
    _, _, steps, _ = _play(env, seed=1)
    assert steps == 40
    assert env.dc.done()
    with pytest.raises(RuntimeError):
        env.step(0)


def test_reward_matches_definition():
    env = DataCenterEnv(num_tasks=60, arrival_rate=6.0)
    _, total, _, info = _play(env, seed=2, actions=lambda i: 0)  # pile everything on one server
    assert info["overload"] > 0
    # energy before the first arrival is spent before any decision, so no reward covers it
    expected = -(config.RL_W_ENERGY * (env.dc.energy_j - env.energy_at_reset_j) / 3600.0) - config.RL_W_SLA * env.dc.violations \
        - config.RL_W_OVERLOAD * env.dc.overload_excess
    assert total == pytest.approx(expected)
    assert info["sla_violations"] == env.dc.violations


def test_env_matches_engine_for_same_decisions():
    env = DataCenterEnv(num_tasks=50)
    _play(env, seed=9)
    engine = run_simulation(INITIAL_16_SERVERS, RoundRobin(), num_tasks=50, seed=9)
    assert env.dc.summary()["total_energy_kwh"] == pytest.approx(engine["total_energy_kwh"])
    assert env.dc.violations == engine["sla_violations"]


def test_invalid_action_rejected():
    env = DataCenterEnv(num_tasks=10)
    env.reset(seed=0)
    with pytest.raises(ValueError):
        env.step(16)


class RecordingRandom(Policy):
    def __init__(self, seed):
        import random
        self.rng = random.Random(seed)
        self.predicted = {}

    def select(self, dc, task):
        idx = self.rng.randrange(len(dc.servers))
        self.predicted[task.task_id] = dc.servers[idx].estimate_start(task.vcpus, dc.t, dc.dt)
        return idx


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_dispatch_time_start_estimate_is_exact(seed):
    from simulation import DataCenter, generate_workload

    policy = RecordingRandom(seed)
    dc = DataCenter(INITIAL_16_SERVERS)
    dc.load(generate_workload(120, seed, arrival_rate=8.0))
    while not dc.done():
        arrived = dc.pop_arrivals()
        if arrived:
            policy.dispatch(dc, arrived)
        dc.tick()
    for task in dc.tasks:
        assert task.start_time == pytest.approx(policy.predicted[task.task_id])
