"""Time-stepped data center model shared by every scheduling policy (and by the RL environment)."""
import heapq
import math
import random
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from config import (
    DEFAULT_ARRIVAL_RATE,
    DT,
    IDLE_TIMEOUT_S,
    MAX_RECORDED_STEPS,
    OVERLOAD_THRESHOLD,
    P_SLEEP_W,
    POWER_CLASSES,
    SLA_DEADLINE_SLACK,
    WAKE_DELAY_S,
    ideal_exec_time,
    is_sla_violation,
    task_deadline,
)


@dataclass
class Task:
    task_id: str
    workload_mi: float
    vcpus: int
    arrival_time: float
    exec_time: float
    deadline: float
    server_idx: int = -1
    start_time: Optional[float] = None
    finish_time: Optional[float] = None
    remaining: float = 0.0


def generate_workload(num_tasks: int, seed: int, arrival_rate: float = DEFAULT_ARRIVAL_RATE,
                      sla_slack: float = SLA_DEADLINE_SLACK) -> List[Task]:
    """Synthetic, seeded workload: Poisson arrivals, three task size classes."""
    rng = random.Random(seed)
    tasks = []
    t = 0.0
    for i in range(1, num_tasks + 1):
        category = rng.random()
        if category < 0.25:
            workload, vcpus = rng.uniform(20_000.0, 50_000.0), rng.choice([1, 2])
        elif category < 0.80:
            workload, vcpus = rng.uniform(60_000.0, 160_000.0), rng.choice([2, 4])
        else:
            workload, vcpus = rng.uniform(180_000.0, 380_000.0), rng.choice([4, 8])
        t += rng.expovariate(arrival_rate)
        tasks.append(Task(
            task_id=f"TSK-{i:04d}",
            workload_mi=workload,
            vcpus=vcpus,
            arrival_time=t,
            exec_time=ideal_exec_time(workload, vcpus),
            deadline=task_deadline(t, workload, vcpus, sla_slack),
        ))
    return tasks


def parse_cores(capacity: str) -> int:
    match = re.search(r"(\d+)\s*v?CPU", capacity, re.IGNORECASE)
    if not match:
        raise ValueError(f"cannot parse core count from capacity {capacity!r}")
    return int(match.group(1))


def power_draw(state: str, utilization: float, p_idle: float, p_max: float) -> float:
    """Watts drawn by a server. utilization is a fraction in [0, 1]."""
    if state == "sleep":
        return P_SLEEP_W
    if state == "waking":
        return p_idle
    u = min(1.0, max(0.0, utilization))
    return p_idle + (p_max - p_idle) * u


class Server:
    def __init__(self, idx: int, server_id: str, capacity: str, rack_id: str):
        self.idx = idx
        self.server_id = server_id
        self.capacity = capacity
        self.rack_id = rack_id
        self.cores = parse_cores(capacity)
        self.p_idle, self.p_max = POWER_CLASSES[self.cores]
        self.reset()

    def reset(self):
        self.state = "on"
        self.wake_left = 0.0
        self.idle_time = 0.0
        self.running: List[Task] = []
        self.queue: deque = deque()
        self.used = 0
        self.tasks_assigned = 0

    @property
    def utilization(self) -> float:
        return self.used / self.cores

    @property
    def queued_cores(self) -> int:
        return sum(t.vcpus for t in self.queue)

    def power(self) -> float:
        return power_draw(self.state, self.utilization, self.p_idle, self.p_max)

    def estimate_start(self, vcpus: int, now: float) -> float:
        """Earliest start for a new task appended to this server's FIFO queue."""
        t = now
        if self.state == "sleep":
            t += WAKE_DELAY_S
        elif self.state == "waking":
            t += self.wake_left
        releases = [(now + task.remaining, task.vcpus) for task in self.running]
        heapq.heapify(releases)
        free = self.cores - self.used

        def wait_for(need: int, at: float):
            nonlocal free
            while free < need:
                release_time, cores = heapq.heappop(releases)
                free += cores
                at = max(at, release_time)
            return at

        for queued in self.queue:
            t = wait_for(queued.vcpus, t)
            free -= queued.vcpus
            heapq.heappush(releases, (t + queued.exec_time, queued.vcpus))
        return wait_for(vcpus, t)


class DataCenter:
    """Servers + clock. Policies call assign(); the loop calls tick() once per DT."""

    def __init__(self, raw_servers: List[Dict[str, Any]], sleep_enabled: bool = True, dt: float = DT):
        self.servers = [Server(i, s["server_id"], s["capacity"], s.get("rack_id", "")) for i, s in enumerate(raw_servers)]
        self.sleep_enabled = sleep_enabled
        self.dt = dt
        self.load([])

    def load(self, tasks: List[Task]):
        for s in self.servers:
            s.reset()
        self.tasks = tasks
        self.arrivals = deque(sorted(tasks, key=lambda t: t.arrival_time))
        self.t = 0.0
        self.ticks = 0
        self.unassigned = len(tasks)
        self.completed = 0
        self.violations = 0
        self.energy_j = 0.0
        self.overload_excess = 0.0  # sum over ticks and servers of max(0, u - threshold) * dt
        n = len(self.servers)
        self.energy_j_by_server = [0.0] * n
        self.busy_core_s = [0.0] * n
        self.awake_s = [0.0] * n
        self.sleep_s = [0.0] * n
        self.idle_s = [0.0] * n
        self.overload_s = [0.0] * n
        self.samples: List[List[tuple]] = []  # per tick: [(util, energy_j, state, queue_len) per server]

    def pop_arrivals(self) -> List[Task]:
        arrived = []
        while self.arrivals and self.arrivals[0].arrival_time <= self.t:
            arrived.append(self.arrivals.popleft())
        return arrived

    def assign(self, task: Task, server_idx: int):
        server = self.servers[server_idx]
        task.server_idx = server_idx
        server.queue.append(task)
        server.tasks_assigned += 1
        server.idle_time = 0.0
        self.unassigned -= 1
        if server.state == "sleep":
            server.state = "waking"
            server.wake_left = WAKE_DELAY_S

    def done(self) -> bool:
        return (self.unassigned == 0 and not self.arrivals
                and all(not s.running and not s.queue for s in self.servers))

    def tick(self):
        dt = self.dt
        for s in self.servers:
            if s.state == "on":
                while s.queue and s.queue[0].vcpus <= s.cores - s.used:
                    task = s.queue.popleft()
                    task.start_time = self.t
                    task.remaining = task.exec_time
                    s.running.append(task)
                    s.used += task.vcpus

        sample = []
        for i, s in enumerate(self.servers):
            u = s.utilization
            e = s.power() * dt
            self.energy_j += e
            self.energy_j_by_server[i] += e
            self.busy_core_s[i] += s.used * dt
            if s.state == "sleep":
                self.sleep_s[i] += dt
            else:
                self.awake_s[i] += dt
                if s.state == "on" and not s.running and not s.queue:
                    self.idle_s[i] += dt
            if u > OVERLOAD_THRESHOLD:
                self.overload_s[i] += dt
                self.overload_excess += (u - OVERLOAD_THRESHOLD) * dt
            sample.append((u, e, s.state, len(s.queue)))
        self.samples.append(sample)

        for s in self.servers:
            still_running = []
            for task in s.running:
                if task.remaining <= dt + 1e-9:
                    task.finish_time = self.t + task.remaining
                    task.remaining = 0.0
                    s.used -= task.vcpus
                    self.completed += 1
                    if is_sla_violation(task.finish_time, task.deadline):
                        self.violations += 1
                else:
                    task.remaining -= dt
                    still_running.append(task)
            s.running = still_running

            if s.state == "waking":
                s.wake_left -= dt
                if s.wake_left <= 1e-9:
                    s.state = "on"
                    s.idle_time = 0.0
            elif s.state == "on":
                if s.running or s.queue:
                    s.idle_time = 0.0
                else:
                    s.idle_time += dt
                    if self.sleep_enabled and s.idle_time >= IDLE_TIMEOUT_S:
                        s.state = "sleep"

        self.t += dt
        self.ticks += 1

    def summary(self) -> Dict[str, Any]:
        horizon = max(self.t, self.dt)
        makespan = max((t.finish_time for t in self.tasks if t.finish_time is not None), default=0.0)
        awake_core_s = sum(self.awake_s[i] * s.cores for i, s in enumerate(self.servers))

        server_stats, servers = [], []
        for i, s in enumerate(self.servers):
            avg_util = 100.0 * self.busy_core_s[i] / (s.cores * horizon)
            sleep_fraction = self.sleep_s[i] / horizon
            awake_util = 100.0 * self.busy_core_s[i] / (s.cores * self.awake_s[i]) if self.awake_s[i] else 0.0
            server_stats.append({
                "server_id": s.server_id,
                "avg_utilization": round(avg_util, 3),
                "energy_kwh": self.energy_j_by_server[i] / 3.6e6,
                "tasks_assigned": s.tasks_assigned,
                "sleep_fraction": round(sleep_fraction, 4),
                "idle_fraction": round(self.idle_s[i] / horizon, 4),
                "overload_fraction": round(self.overload_s[i] / horizon, 4),
                "flags": "",
            })
            servers.append({
                "server_id": s.server_id,
                "current_utilization": round(awake_util, 1),
                "status": "active" if s.tasks_assigned else "idle",
                "power_state": "sleep" if sleep_fraction >= 0.5 else "on",
                "temperature_c": round(28.0 + 36.0 * awake_util / 100.0, 1),
                "power_draw_w": round(self.energy_j_by_server[i] / horizon, 1),
                "active_workloads": s.tasks_assigned,
            })

        return {
            "makespan": round(makespan, 3),
            "total_energy_kwh": self.energy_j / 3.6e6,
            "avg_utilization": round(100.0 * sum(self.busy_core_s) / awake_core_s, 3) if awake_core_s else 0.0,
            "sla_violations": self.violations,
            "server_stats": server_stats,
            "step_metrics": self._downsampled_steps(),
            "servers": servers,
        }

    def _downsampled_steps(self) -> List[Dict[str, Any]]:
        n = len(self.samples)
        if n == 0:
            return []
        bucket = math.ceil(n / MAX_RECORDED_STEPS)
        rows = []
        for step, start in enumerate(range(0, n, bucket), start=1):
            window = self.samples[start:start + bucket]
            end_time = (start + len(window)) * self.dt
            for i, s in enumerate(self.servers):
                cells = [tick[i] for tick in window]
                rows.append({
                    "step": step,
                    "timestamp": round(end_time, 3),
                    "server_id": s.server_id,
                    "utilization": round(100.0 * sum(c[0] for c in cells) / len(cells), 3),
                    "energy_kwh": sum(c[1] for c in cells) / 3.6e6,
                    "power_state": cells[-1][2],
                    "queue_len": cells[-1][3],
                })
        return rows


def run_simulation(
    raw_servers: List[Dict[str, Any]],
    policy,
    num_tasks: int,
    seed: int,
    sleep_enabled: bool = True,
    sla_slack: float = SLA_DEADLINE_SLACK,
    arrival_rate: float = DEFAULT_ARRIVAL_RATE,
    progress_cb: Optional[Callable[[float], None]] = None,
    progress_every: int = 25,
) -> Dict[str, Any]:
    dc = DataCenter(raw_servers, sleep_enabled=sleep_enabled)
    dc.load(generate_workload(num_tasks, seed, arrival_rate, sla_slack))
    while not dc.done():
        arrived = dc.pop_arrivals()
        if arrived:
            policy.dispatch(dc, arrived)
        dc.tick()
        if progress_cb and dc.ticks % progress_every == 0:
            progress_cb(dc.completed / max(1, num_tasks))
    return dc.summary()
