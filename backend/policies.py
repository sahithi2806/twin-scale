"""Scheduling policies. Every policy sees the same DataCenter state and dispatches arrived tasks to servers."""
import os
from typing import List

from config import OVERLOAD_THRESHOLD, is_sla_violation
from simulation import DataCenter, Task

DEFAULT_WEIGHTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "dqn.pt")


class PolicyUnavailable(Exception):
    """Raised when a policy cannot run, e.g. DQN weights have not been trained yet."""


class Policy:
    name = ""

    def dispatch(self, dc: DataCenter, tasks: List[Task]):
        for task in tasks:
            dc.assign(task, self.select(dc, task))

    def select(self, dc: DataCenter, task: Task) -> int:
        raise NotImplementedError


class MinMinPolicy(Policy):
    """Online batch Min-Min: among the tasks that arrived this tick, repeatedly place the
    (task, server) pair with the smallest estimated completion time. Ties go to the
    least-utilized server, which is what Min-Min's makespan objective implies."""

    name = "min-min"

    def _best_server(self, dc: DataCenter, task: Task, starts: dict):
        best = None
        for s in dc.servers:
            k = (s.idx, task.vcpus)
            if k not in starts:
                starts[k] = s.estimate_start(task.vcpus, dc.t, dc.dt)
            key = (round(starts[k] + task.exec_time, 9), s.utilization + s.queued_cores / s.cores, s.idx)
            if best is None or key < best:
                best = key
        return best

    def dispatch(self, dc: DataCenter, tasks: List[Task]):
        remaining = list(tasks)
        starts: dict = {}  # (server, vCPUs) -> start estimate; only the server that just got a task changes
        while remaining:
            choice = None
            for ti, task in enumerate(remaining):
                key = self._best_server(dc, task, starts)
                if choice is None or key[0] < choice[0][0]:
                    choice = (key, ti)
            (_, _, server_idx), ti = choice
            dc.assign(remaining.pop(ti), server_idx)
            for k in [k for k in starts if k[0] == server_idx]:
                del starts[k]

    def select(self, dc: DataCenter, task: Task) -> int:
        return self._best_server(dc, task, {})[2]


class PowerAwarePolicy(Policy):
    """Best-fit consolidation: keep work on servers that are already busy so the rest can sleep.
    1. Awake server that can start the task now without exceeding OVERLOAD_THRESHOLD: prefer busy
       servers, then the tightest fit, then the most power-efficient (lowest P_max per core).
    2. Otherwise the earliest-finishing awake server, if that still meets the deadline.
    3. Otherwise wake the most efficient sleeping server.
    4. Otherwise the earliest-finishing server overall."""

    name = "power-aware"

    def select(self, dc: DataCenter, task: Task) -> int:
        best = None
        for s in dc.servers:
            committed = s.used + s.queued_cores + task.vcpus
            if s.state == "sleep" or s.queue or committed > OVERLOAD_THRESHOLD * s.cores:
                continue
            key = (s.used == 0 and s.state == "on", -committed / s.cores, s.p_max / s.cores, s.idx)
            if best is None or key < best:
                best = key
        if best is not None:
            return best[-1]

        def ect(s):
            return s.estimate_start(task.vcpus, dc.t, dc.dt) + task.exec_time

        awake = [s for s in dc.servers if s.state != "sleep"]
        if awake:
            fastest = min(awake, key=lambda s: (ect(s), s.idx))
            if not is_sla_violation(ect(fastest), task.deadline):
                return fastest.idx
        sleepers = [s for s in dc.servers if s.state == "sleep"]
        if sleepers:
            return min(sleepers, key=lambda s: (s.p_max / s.cores, s.idx)).idx
        return min(dc.servers, key=lambda s: (ect(s), s.idx)).idx


class DQNPolicy(Policy):
    """Greedy policy from a trained Q-network. Inference only: weights come from train_dqn.py."""

    name = "dqn"

    def __init__(self, net, metadata):
        self.net = net
        self.metadata = metadata

    def select(self, dc: DataCenter, task: Task) -> int:
        from rl.dqn_agent import greedy_action
        from rl.env import build_observation

        return greedy_action(self.net, build_observation(dc, task))


_dqn_cache: dict = {}


def weights_path() -> str:
    return os.environ.get("DCTWIN_DQN_WEIGHTS", DEFAULT_WEIGHTS_PATH)


def load_dqn_policy() -> DQNPolicy:
    path = weights_path()
    if not os.path.exists(path):
        raise PolicyUnavailable(f"DQN weights not found at {path} - run `python train_dqn.py` in backend/ first.")
    key = (path, os.path.getmtime(path))
    if key not in _dqn_cache:
        from rl.dqn_agent import load_q_network
        from rl.env import env_signature

        net, ckpt = load_q_network(path)
        metadata = ckpt.get("metadata", {})
        if metadata.get("env_signature") != env_signature():
            raise PolicyUnavailable(
                "DQN weights were trained for a different engine configuration - rerun `python train_dqn.py`.")
        _dqn_cache.clear()
        _dqn_cache[key] = DQNPolicy(net, metadata)
    return _dqn_cache[key]


POLICY_NAMES = ("min-min", "power-aware", "dqn")


def get_policy(name: str) -> Policy:
    if name == "min-min":
        return MinMinPolicy()
    if name == "power-aware":
        return PowerAwarePolicy()
    if name == "dqn":
        return load_dqn_policy()
    raise ValueError(f"unknown policy {name!r}")
