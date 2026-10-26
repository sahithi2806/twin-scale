"""Scheduling policies. Every policy sees the same DataCenter state and dispatches arrived tasks to servers."""
import os
from typing import List

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

    def _best_server(self, dc: DataCenter, task: Task):
        best = None
        for s in dc.servers:
            ect = s.estimate_start(task.vcpus, dc.t) + task.exec_time
            key = (round(ect, 9), s.utilization + s.queued_cores / s.cores, s.idx)
            if best is None or key < best:
                best = key
        return best

    def dispatch(self, dc: DataCenter, tasks: List[Task]):
        remaining = list(tasks)
        while remaining:
            choice = None
            for ti, task in enumerate(remaining):
                key = self._best_server(dc, task)
                if choice is None or key[0] < choice[0][0]:
                    choice = (key, ti)
            (_, _, server_idx), ti = choice
            dc.assign(remaining.pop(ti), server_idx)

    def select(self, dc: DataCenter, task: Task) -> int:
        return self._best_server(dc, task)[2]


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


POLICY_NAMES = ("min-min", "dqn")


def get_policy(name: str) -> Policy:
    if name == "min-min":
        return MinMinPolicy()
    if name == "dqn":
        return load_dqn_policy()
    raise ValueError(f"unknown policy {name!r}")
