import numpy as np
import random
from typing import List, Dict, Any, Tuple
from simulation import VirtualServer, Task
from config import task_deadline, is_sla_violation

class SimpleQNetwork:
    """
    Multi-Layer Perceptron (MLP) Q-Network implemented with NumPy.
    State dimension: 35 features (CPU utilization & power states of 16 servers + task requirements)
    Output: 16 Q-values representing expected return for assigning task to each server.
    """
    def __init__(self, state_dim: int = 35, hidden_dim: int = 64, action_dim: int = 16, lr: float = 0.01, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.lr = lr
        self.W1 = self.rng.randn(state_dim, hidden_dim) * np.sqrt(2.0 / state_dim)
        self.b1 = np.zeros((1, hidden_dim))
        self.W2 = self.rng.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros((1, hidden_dim))
        self.W3 = self.rng.randn(hidden_dim, action_dim) * np.sqrt(2.0 / hidden_dim)
        self.b3 = np.zeros((1, action_dim))

    def forward(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if state.ndim == 1:
            state = state.reshape(1, -1)
        z1 = np.dot(state, self.W1) + self.b1
        a1 = np.maximum(0, z1)
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = np.maximum(0, z2)
        q_values = np.dot(a2, self.W3) + self.b3
        return q_values, a1, a2

    def train_step(self, state: np.ndarray, action: int, target_q: float):
        """Single backpropagation step minimizing MSE loss on chosen action."""
        if state.ndim == 1:
            state = state.reshape(1, -1)
        q_vals, a1, a2 = self.forward(state)
        current_q = q_vals[0, action]
        td_error = current_q - target_q

        grad_out = np.zeros_like(q_vals)
        grad_out[0, action] = td_error

        dW3 = np.dot(a2.T, grad_out)
        db3 = np.sum(grad_out, axis=0, keepdims=True)

        da2 = np.dot(grad_out, self.W3.T)
        dz2 = da2 * (a2 > 0)
        dW2 = np.dot(a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)

        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * (a1 > 0)
        dW1 = np.dot(state.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)

        clip = 1.0
        self.W3 -= self.lr * np.clip(dW3, -clip, clip)
        self.b3 -= self.lr * np.clip(db3, -clip, clip)
        self.W2 -= self.lr * np.clip(dW2, -clip, clip)
        self.b2 -= self.lr * np.clip(db2, -clip, clip)
        self.W1 -= self.lr * np.clip(dW1, -clip, clip)
        self.b1 -= self.lr * np.clip(db1, -clip, clip)


class DQNScheduler:
    """
    Reinforcement Learning (DQN) Scheduler:
    - State Space: CPU utilization and power state ratios across all 16 servers + task characteristics.
    - Action Space: 16 discrete actions mapping to the available virtual servers.
    - Reward Function: Minimizes energy consumption, penalizes SLA deadline misses and server overloading (>82%),
      and rewards workload consolidation to keep unneeded servers in low-power sleep states.
    """
    def __init__(self, action_dim: int = 16, gamma: float = 0.95, epsilon: float = 0.1, seed: int = 42):
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.state_dim = 16 * 2 + 3
        self.q_net = SimpleQNetwork(state_dim=self.state_dim, hidden_dim=64, action_dim=action_dim, seed=seed)
        self.rng = random.Random(seed)

    def extract_state(self, servers: List[VirtualServer], task: Task) -> np.ndarray:
        features = []
        for s in servers:
            u = s.current_utilization / 100.0
            p_ratio = s.get_power_draw(s.current_utilization) / max(1.0, s.max_power_w)
            features.extend([u, p_ratio])

        workload_norm = min(1.0, task.workload_mi / 350000.0)
        vcpus_norm = min(1.0, task.vcpus / 8.0)
        ideal_time = task.workload_mi / (task.vcpus * 2500.0)
        sla_factor = min(2.0, (task.arrival_time + ideal_time * 1.5) / 100.0)
        features.extend([workload_norm, vcpus_norm, sla_factor])
        return np.array(features, dtype=np.float32)

    def compute_placement_reward(
        self,
        server: VirtualServer,
        task: Task,
        start_time: float,
        finish_time: float,
        sla_deadline: float,
        new_util: float,
        prev_util: float
    ) -> float:
        incremental_w = server.get_power_draw(new_util) - server.get_power_draw(prev_util)
        duration_s = max(1.0, finish_time - start_time)
        energy_penalty = -0.005 * (incremental_w * duration_s / 3600.0)

        overload_penalty = 0.0
        if new_util > 82.0:
            overload_penalty = -4.0 * ((new_util - 82.0) / 18.0)
        elif 45.0 <= new_util <= 80.0:
            overload_penalty = +1.2

        sla_penalty = 0.0
        if finish_time > sla_deadline:
            lateness = finish_time - sla_deadline
            sla_penalty = -5.0 * (1.0 + (lateness / max(1.0, sla_deadline)))
        else:
            sla_penalty = +1.5

        consolidation_bonus = 0.0
        if prev_util > 0.0 and new_util <= 80.0:
            consolidation_bonus = +2.0
        elif prev_util == 0.0:
            consolidation_bonus = -1.0

        return energy_penalty + overload_penalty + sla_penalty + consolidation_bonus

    def schedule(self, tasks: List[Task], servers: List[VirtualServer], sla_slack: float) -> Tuple[float, int, List[Dict[str, Any]]]:
        for s in servers:
            s.reset_state()

        task_records = []
        sla_violations = 0

        # Efficiency ranks: servers with best compute throughput per watt
        efficiency_ranks = sorted(range(len(servers)), key=lambda idx: servers[idx].max_power_w / max(1, servers[idx].cores))
        # Active consolidated cluster: top 11 power-efficient nodes; 5 nodes kept in deep sleep (18W)
        active_pool_size = 11
        preferred_cluster = set(efficiency_ranks[:active_pool_size])

        # Multicore parallel execution slots per server
        server_slots = {
            s_idx: [0.0] * max(2, min(6, servers[s_idx].cores // 20))
            for s_idx in range(len(servers))
        }

        for task_idx, task in enumerate(tasks):
            sla_deadline = task_deadline(task.arrival_time, task.workload_mi, task.vcpus, sla_slack)
            state = self.extract_state(servers, task)

            q_values, _, _ = self.q_net.forward(state)
            q_scores = q_values[0].copy()

            for s_idx in preferred_cluster:
                server = servers[s_idx]
                exec_time = server.execution_time_for_task(task)
                earliest_slot_time = min(server_slots[s_idx])
                st = max(earliest_slot_time, task.arrival_time)
                ft = st + exec_time

                min_cluster_ready = min(min(server_slots[i]) for i in preferred_cluster)
                queue_latency = max(0.0, earliest_slot_time - min_cluster_ready)
                q_scores[s_idx] -= 0.08 * queue_latency

                if ft > sla_deadline:
                    q_scores[s_idx] -= 12.0
                
                # Favor energy-efficient high-core servers (128C and 96C)
                q_scores[s_idx] += (server.cores / 32.0) * 1.5

                if server.current_utilization > 80.0:
                    q_scores[s_idx] -= 6.0

            # Restrict action candidates to preferred cluster to enforce sleep on cold nodes
            candidate_actions = list(preferred_cluster)
            action = int(candidate_actions[int(np.argmax([q_scores[i] for i in candidate_actions]))])
            chosen_server = servers[action]

            # Assign to earliest available core slot
            slots = server_slots[action]
            slot_idx = int(np.argmin(slots))
            exec_time = chosen_server.execution_time_for_task(task)
            start_time = max(slots[slot_idx], task.arrival_time)
            finish_time = start_time + exec_time
            slots[slot_idx] = finish_time
            chosen_server.ready_time = round(max(slots), 2)

            prev_util = chosen_server.current_utilization
            active_cores = task.vcpus + sum(t.vcpus for t in chosen_server.assigned_tasks if t.finish_time > start_time)
            ratio = active_cores / max(1, chosen_server.cores)
            new_util = min(88.0, max(28.0, ratio * 65.0 + 20.0))

            is_sla_violated = is_sla_violation(finish_time, sla_deadline)
            if is_sla_violated:
                sla_violations += 1

            reward = self.compute_placement_reward(
                chosen_server, task, start_time, finish_time, sla_deadline, new_util, prev_util
            )

            task.assigned_server_id = chosen_server.server_id
            task.start_time = round(start_time, 2)
            task.finish_time = round(finish_time, 2)
            chosen_server.assigned_tasks.append(task)
            chosen_server.current_utilization = round(new_util, 1)

            next_state = self.extract_state(servers, task)
            next_q, _, _ = self.q_net.forward(next_state)
            target = reward + self.gamma * np.max(next_q)
            self.q_net.train_step(state, action, target)

            task_records.append({
                "task_id": task.task_id,
                "server_id": chosen_server.server_id,
                "start_time": task.start_time,
                "finish_time": task.finish_time,
                "deadline": sla_deadline,
                "sla_violated": is_sla_violated,
                "reward": round(reward, 2)
            })

        makespan = max((s.ready_time for s in servers), default=1.0)
        return round(makespan, 2), sla_violations, task_records
