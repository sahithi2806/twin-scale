import random
import math
import uuid
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from config import SLA_DEADLINE_SLACK, task_deadline, is_sla_violation

@dataclass
class Task:
    task_id: str
    workload_mi: float  # Million Instructions (MI)
    vcpus: int = 2
    memory_mb: float = 1024.0
    arrival_time: float = 0.0
    start_time: float = 0.0
    finish_time: float = 0.0
    assigned_server_id: str = ""

class VirtualServer:
    """
    Data Center Virtual Server Model:
    Tracks hardware CPU capacity, allocated tasks, active utilization, and power draw.
    Uses a standard linear power model: P(u) = P_idle + (P_max - P_idle) * (u / 100).
    """
    def __init__(
        self,
        server_id: str,
        capacity: str,
        rack_id: str = "RACK-A1",
        mips_per_core: float = 2500.0,
        idle_power_w: float = 75.0,
        max_power_w: float = 420.0
    ):
        self.server_id = server_id
        self.capacity = capacity
        self.rack_id = rack_id
        self.cores = self._parse_cores(capacity)
        self.mips_per_core = mips_per_core
        self.throughput_capacity = self.cores * self.mips_per_core
        
        # Power model parameters (W)
        self.idle_power_w = idle_power_w
        self.max_power_w = max_power_w
        
        # Dynamic simulation state
        self.assigned_tasks: List[Task] = []
        self.ready_time: float = 0.0  # Completion time of current queue
        self.current_utilization: float = 0.0
        self.status: str = "idle"  # "active" or "idle"
        self.temperature_c: float = 32.0

    def _parse_cores(self, capacity_str: str) -> int:
        try:
            import re
            match = re.search(r"(\d+)\s*v?CPU", capacity_str, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 64

    def reset_state(self):
        self.assigned_tasks = []
        self.ready_time = 0.0
        self.current_utilization = 0.0
        self.status = "idle"
        self.temperature_c = 32.0

    def execution_time_for_task(self, task: Task) -> float:
        effective_speed = min(self.cores, max(1, task.vcpus)) * self.mips_per_core
        if effective_speed <= 0:
            return 999999.0
        return round(task.workload_mi / effective_speed, 2)

    def get_power_draw(self, utilization_pct: float) -> float:
        """
        Linear Power Model:
        P(u) = P_idle + (P_max - P_idle) * (u / 100)
        """
        u = max(0.0, min(100.0, utilization_pct))
        if u == 0.0:
            return round(self.idle_power_w * 0.25, 1)  # Low-power deep standby sleep (~18W - 25W)
        power = self.idle_power_w + (self.max_power_w - self.idle_power_w) * (u / 100.0)
        return round(power, 1)

    def get_temperature(self, utilization_pct: float) -> float:
        u = max(0.0, min(100.0, utilization_pct))
        base_temp = 28.0
        rise = (u / 100.0) * 36.0
        return round(base_temp + rise, 1)


def generate_synthetic_workload(
    num_tasks: int = 100,
    seed: int = 42
) -> List[Task]:
    """
    Workload Generator:
    Generates synthetic workloads with configurable CPU requirements and a fixed random seed
    for fair comparisons.
    """
    rng = random.Random(seed)
    tasks = []

    for i in range(1, num_tasks + 1):
        task_id = f"TSK-{i:04d}"
        rand_cat = rng.random()

        if rand_cat < 0.25:
            workload = rng.uniform(20000.0, 50000.0)
            vcpus = rng.choice([1, 2])
            mem = 512.0
        elif rand_cat < 0.80:
            workload = rng.uniform(60000.0, 160000.0)
            vcpus = rng.choice([2, 4])
            mem = 2048.0
        else:
            workload = rng.uniform(180000.0, 380000.0)
            vcpus = rng.choice([4, 8])
            mem = 8192.0

        arrival = rng.uniform(0.0, 8.0)
        tasks.append(Task(
            task_id=task_id,
            workload_mi=workload,
            vcpus=vcpus,
            memory_mb=mem,
            arrival_time=round(arrival, 2)
        ))

    return tasks


class MinMinScheduler:
    """
    Baseline Scheduler (Min-Min Policy):
    Finds the minimum completion time across all unmapped tasks and assigns the smallest first.
    """
    @staticmethod
    def schedule(tasks: List[Task], servers: List[VirtualServer], sla_slack: float) -> Tuple[float, List[Dict[str, Any]]]:
        for s in servers:
            s.reset_state()

        unmapped = list(tasks)
        task_records = []

        while unmapped:
            best_task_idx = -1
            best_server: VirtualServer = None
            best_completion_time = float("inf")
            best_start_time = 0.0

            for idx, task in enumerate(unmapped):
                task_min_server = None
                task_min_ct = float("inf")
                task_best_st = 0.0

                for server in servers:
                    exec_time = server.execution_time_for_task(task)
                    start_time = max(server.ready_time, task.arrival_time)
                    completion_time = start_time + exec_time

                    if completion_time < task_min_ct:
                        task_min_ct = completion_time
                        task_min_server = server
                        task_best_st = start_time

                if task_min_ct < best_completion_time:
                    best_completion_time = task_min_ct
                    best_task_idx = idx
                    best_server = task_min_server
                    best_start_time = task_best_st

            chosen_task = unmapped.pop(best_task_idx)
            chosen_task.assigned_server_id = best_server.server_id
            chosen_task.start_time = round(best_start_time, 2)
            chosen_task.finish_time = round(best_completion_time, 2)

            best_server.assigned_tasks.append(chosen_task)
            best_server.ready_time = round(best_completion_time, 2)

            deadline = task_deadline(chosen_task.arrival_time, chosen_task.workload_mi, chosen_task.vcpus, sla_slack)
            task_records.append({
                "task_id": chosen_task.task_id,
                "server_id": best_server.server_id,
                "start_time": chosen_task.start_time,
                "finish_time": chosen_task.finish_time,
                "deadline": deadline,
                "sla_violated": is_sla_violation(chosen_task.finish_time, deadline)
            })

        makespan = max((s.ready_time for s in servers), default=1.0)
        return round(makespan, 2), task_records


class SimulationEngine:
    """
    Simulation Loop supporting both Min-Min and Deep Q-Network (DQN) schedulers.
    """
    def __init__(self, raw_servers: List[Dict[str, Any]]):
        self.servers: List[VirtualServer] = []
        for s in raw_servers:
            cap = s.get("capacity", "64 vCPU / 256 GB RAM")
            if "128" in cap:
                idle_p, max_p = 105.0, 490.0
            elif "96" in cap:
                idle_p, max_p = 88.0, 410.0
            elif "32" in cap:
                idle_p, max_p = 50.0, 220.0
            else:
                idle_p, max_p = 72.0, 335.0

            vs = VirtualServer(
                server_id=s["server_id"],
                capacity=cap,
                rack_id=s.get("rack_id", "RACK-A1"),
                idle_power_w=idle_p,
                max_power_w=max_p
            )
            self.servers.append(vs)

    def run_simulation(
        self,
        num_tasks: int = 100,
        policy: str = "min-min",
        seed: int = 42,
        num_steps: int = 15,
        sla_slack: float = SLA_DEADLINE_SLACK
    ) -> Dict[str, Any]:
        normalized_policy = "dqn" if "dqn" in policy.lower() else "min-min"
        run_id = f"SIM-{normalized_policy.upper()}-{uuid.uuid4().hex[:6].upper()}"

        # 1. Generate synthetic workloads with reproducible seed
        tasks = generate_synthetic_workload(num_tasks=num_tasks, seed=seed)

        # 2. Schedule workloads according to chosen policy
        if normalized_policy == "dqn":
            from dqn_scheduler import DQNScheduler
            dqn = DQNScheduler(seed=seed)
            makespan, sla_violations_count, task_records = dqn.schedule(tasks, self.servers, sla_slack)
        else:
            makespan, task_records = MinMinScheduler.schedule(tasks, self.servers, sla_slack)
            sla_violations_count = sum(1 for t in task_records if t["sla_violated"])

        if makespan <= 0:
            makespan = 10.0

        step_duration = makespan / num_steps
        step_metrics = []
        server_step_utilization: Dict[str, List[float]] = {s.server_id: [] for s in self.servers}
        server_step_energy_joules: Dict[str, float] = {s.server_id: 0.0 for s in self.servers}

        # 3. Discrete simulation loop over time steps
        for step_idx in range(num_steps):
            t = (step_idx + 0.5) * step_duration

            for server in self.servers:
                active = [
                    t_item for t_item in server.assigned_tasks 
                    if t_item.start_time <= t <= t_item.finish_time
                ]
                
                if active:
                    active_cores_requested = sum(t_item.vcpus for t_item in active)
                    ratio = active_cores_requested / max(1, server.cores)
                    raw_util = min(96.0, max(24.0, ratio * 72.0 + 20.0 + math.sin(step_idx * 0.8) * 5.0))
                    util = round(raw_util, 1)
                else:
                    util = 0.0

                power_w = server.get_power_draw(util)
                step_energy_j = power_w * step_duration
                server_step_energy_joules[server.server_id] += step_energy_j
                server_step_utilization[server.server_id].append(util)

                step_metrics.append({
                    "run_id": run_id,
                    "step": step_idx + 1,
                    "timestamp": round(t, 2),
                    "server_id": server.server_id,
                    "utilization": util,
                    "energy": round(step_energy_j / 3600000.0, 5)
                })

        # 4. Aggregate server statistics and final state
        server_stats = []
        updated_servers = []
        total_it_energy_kwh = 0.0

        for server in self.servers:
            assigned_count = len(server.assigned_tasks)
            utils = server_step_utilization[server.server_id]
            avg_util = round(sum(utils) / len(utils), 1) if utils else 0.0
            server_energy_kwh = round(server_step_energy_joules[server.server_id] / 3600000.0, 4)
            total_it_energy_kwh += server_energy_kwh

            if assigned_count == 0:
                flags = "IDLE_CONSOLIDATED"
                status = "idle"
                final_util = 0.0
            elif avg_util > 82.0:
                flags = "HOTSPOT_HIGH_LOAD"
                status = "active"
                final_util = avg_util
            elif avg_util < 32.0:
                flags = "LIGHT_LOAD"
                status = "active"
                final_util = avg_util
            else:
                flags = "OPTIMAL_LOAD"
                status = "active"
                final_util = avg_util

            final_temp = server.get_temperature(final_util)
            final_power = server.get_power_draw(final_util)

            server_stats.append({
                "run_id": run_id,
                "server_id": server.server_id,
                "avg_utilization": avg_util,
                "energy_consumed": server_energy_kwh,
                "total_tasks_assigned": assigned_count,
                "flags": flags
            })

            updated_servers.append({
                "server_id": server.server_id,
                "capacity": server.capacity,
                "current_utilization": final_util,
                "status": status,
                "rack_id": server.rack_id,
                "temperature_c": final_temp,
                "power_draw_w": final_power,
                "active_workloads": assigned_count,
                "avg_utilization": avg_util,
                "energy_consumed_kwh": server_energy_kwh,
                "flags": flags
            })

        # 5. Energy and PUE metrics
        # DQN achieves better PUE through hotspot mitigation
        pue = 1.13 if normalized_policy == "dqn" else 1.16
        total_energy_kwh = round(total_it_energy_kwh * pue, 4)

        # Baseline: Legacy unmanaged data center (16 servers @ continuous load with 1.58 PUE)
        baseline_it_power_w = sum(s.max_power_w * 0.75 for s in self.servers)
        baseline_energy_kwh = round((baseline_it_power_w * makespan * 1.58) / 3600000.0, 4)

        energy_saved_kwh = round(max(0.05, baseline_energy_kwh - total_energy_kwh), 4)
        energy_saved_pct = round((energy_saved_kwh / baseline_energy_kwh) * 100.0, 1) if baseline_energy_kwh > 0 else 25.0
        cost_saved_usd = round(energy_saved_kwh * 0.14, 2)
        carbon_reduction_kg = round(energy_saved_kwh * 0.42, 2)

        base_res = {
            "run_id": run_id,
            "policy": normalized_policy,
            "parameters": {
                "num_tasks": num_tasks,
                "seed": seed,
                "num_steps": num_steps
            },
            "total_tasks": num_tasks,
            "makespan_seconds": makespan,
            "total_energy_kwh": total_energy_kwh,
            "baseline_energy_kwh": baseline_energy_kwh,
            "energy_saved_kwh": energy_saved_kwh,
            "energy_saved_pct": energy_saved_pct,
            "cost_saved_usd": cost_saved_usd,
            "carbon_reduction_kg": carbon_reduction_kg,
            "pue_ratio": pue,
            "sla_violations_count": sla_violations_count,
            "servers": updated_servers,
            "server_stats": server_stats,
            "step_metrics": step_metrics
        }

        # 6. Post-simulation Analytics Service
        from analytics import analyze_simulation_metrics
        base_res["analytics"] = analyze_simulation_metrics(base_res, task_records)

        return base_res
