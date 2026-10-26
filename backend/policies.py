"""Scheduling policies. Every policy sees the same DataCenter state and dispatches arrived tasks to servers."""
from typing import List

from simulation import DataCenter, Task


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


POLICY_NAMES = ("min-min", "dqn")


def get_policy(name: str) -> Policy:
    if name == "min-min":
        return MinMinPolicy()
    if name == "dqn":
        raise PolicyUnavailable("DQN weights not found - run `python train_dqn.py` in backend/ first.")
    raise ValueError(f"unknown policy {name!r}")
