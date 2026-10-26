"""Gym-style environment over the shared DataCenter engine. One decision = place the next arrived task."""
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config import (
    DEFAULT_ARRIVAL_RATE,
    RL_W_ENERGY,
    RL_W_OVERLOAD,
    RL_W_SLA,
    SLA_DEADLINE_SLACK,
)
from database import INITIAL_16_SERVERS
from simulation import DataCenter, Task, generate_workload

POWER_STATE_CODE = {"sleep": 0.0, "waking": 0.5, "on": 1.0}
MAX_VCPUS = 8.0
DEADLINE_SCALE_S = 60.0
QUEUE_SCALE = 10.0


def observation_size(num_servers: int) -> int:
    return 3 * num_servers + 2


def build_observation(dc: DataCenter, task: Optional[Task]) -> np.ndarray:
    """[util x N, power state x N, queue length x N, next task vCPU demand, next task time-to-deadline]"""
    util = [s.utilization for s in dc.servers]
    state = [POWER_STATE_CODE[s.state] for s in dc.servers]
    queue = [min(1.0, len(s.queue) / QUEUE_SCALE) for s in dc.servers]
    if task is None:
        task_feats = [0.0, 0.0]
    else:
        task_feats = [task.vcpus / MAX_VCPUS, float(np.clip((task.deadline - dc.t) / DEADLINE_SCALE_S, -1.0, 1.0))]
    return np.asarray(util + state + queue + task_feats, dtype=np.float32)


class DataCenterEnv:
    def __init__(self, raw_servers: Optional[List[Dict[str, Any]]] = None, num_tasks: int = 200,
                 sleep_enabled: bool = True, sla_slack: float = SLA_DEADLINE_SLACK,
                 arrival_rate: float = DEFAULT_ARRIVAL_RATE):
        self.raw_servers = raw_servers or INITIAL_16_SERVERS
        self.num_tasks = num_tasks
        self.sleep_enabled = sleep_enabled
        self.sla_slack = sla_slack
        self.arrival_rate = arrival_rate
        self.n_actions = len(self.raw_servers)
        self.obs_size = observation_size(self.n_actions)
        self.dc: Optional[DataCenter] = None
        self.pending: deque = deque()

    def reset(self, seed: int) -> np.ndarray:
        self.dc = DataCenter(self.raw_servers, sleep_enabled=self.sleep_enabled)
        self.dc.load(generate_workload(self.num_tasks, seed, self.arrival_rate, self.sla_slack))
        self.pending = deque(self.dc.pop_arrivals())
        if not self.pending:
            self._advance()
        return self._obs()

    def _advance(self):
        while not self.dc.done():
            self.dc.tick()
            self.pending.extend(self.dc.pop_arrivals())
            if self.pending:
                return

    def _obs(self) -> np.ndarray:
        return build_observation(self.dc, self.pending[0] if self.pending else None)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        if not self.pending:
            raise RuntimeError("step() called on a finished episode; call reset()")
        if not 0 <= action < self.n_actions:
            raise ValueError(f"action {action} out of range")
        energy_before = self.dc.energy_j
        violations_before = self.dc.violations
        overload_before = self.dc.overload_excess

        self.dc.assign(self.pending.popleft(), int(action))
        if not self.pending:
            self._advance()

        energy_wh = (self.dc.energy_j - energy_before) / 3600.0
        violations = self.dc.violations - violations_before
        overload = self.dc.overload_excess - overload_before
        reward = -(RL_W_ENERGY * energy_wh) - RL_W_SLA * violations - RL_W_OVERLOAD * overload
        done = not self.pending
        info = {"energy_wh": energy_wh, "sla_violations": violations, "overload": overload, "time": self.dc.t}
        return self._obs(), float(reward), done, info
