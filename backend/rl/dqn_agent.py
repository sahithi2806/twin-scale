"""Minimal DQN (MLP Q-network, replay buffer, target network, epsilon-greedy). CPU only."""
from typing import Any, Dict, Optional

import numpy as np
import torch
from torch import nn

DEVICE = torch.device("cpu")


class QNetwork(nn.Module):
    def __init__(self, obs_size: int, n_actions: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_size, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ReplayBuffer:
    def __init__(self, capacity: int, obs_size: int, seed: int = 0):
        self.capacity = capacity
        self.obs = np.zeros((capacity, obs_size), dtype=np.float32)
        self.next_obs = np.zeros((capacity, obs_size), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)
        self.size = 0
        self.pos = 0
        self.rng = np.random.default_rng(seed)

    def add(self, obs, action, reward, next_obs, done):
        i = self.pos
        self.obs[i], self.actions[i], self.rewards[i] = obs, action, reward
        self.next_obs[i], self.dones[i] = next_obs, float(done)
        self.pos = (self.pos + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int):
        idx = self.rng.integers(0, self.size, size=batch_size)
        return (torch.from_numpy(self.obs[idx]), torch.from_numpy(self.actions[idx]),
                torch.from_numpy(self.rewards[idx]), torch.from_numpy(self.next_obs[idx]),
                torch.from_numpy(self.dones[idx]))

    def __len__(self):
        return self.size


class DQNAgent:
    def __init__(self, obs_size: int, n_actions: int, hidden: int = 128, lr: float = 3e-4, gamma: float = 0.99,
                 buffer_size: int = 50_000, batch_size: int = 64, target_sync: int = 500,
                 eps_start: float = 1.0, eps_end: float = 0.05, eps_decay_steps: int = 20_000,
                 learn_start: int = 1_000, seed: int = 0):
        torch.manual_seed(seed)
        self.obs_size, self.n_actions, self.hidden = obs_size, n_actions, hidden
        self.gamma, self.batch_size, self.target_sync = gamma, batch_size, target_sync
        self.eps_start, self.eps_end, self.eps_decay_steps = eps_start, eps_end, eps_decay_steps
        self.learn_start = learn_start
        self.q = QNetwork(obs_size, n_actions, hidden).to(DEVICE)
        self.target = QNetwork(obs_size, n_actions, hidden).to(DEVICE)
        self.target.load_state_dict(self.q.state_dict())
        self.target.eval()
        self.optimizer = torch.optim.Adam(self.q.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_size, obs_size, seed)
        self.rng = np.random.default_rng(seed + 1)
        self.steps = 0
        self.updates = 0

    @property
    def epsilon(self) -> float:
        frac = min(1.0, self.steps / max(1, self.eps_decay_steps))
        return self.eps_start + frac * (self.eps_end - self.eps_start)

    def act(self, obs: np.ndarray, greedy: bool = False) -> int:
        if not greedy and self.rng.random() < self.epsilon:
            return int(self.rng.integers(self.n_actions))
        return greedy_action(self.q, obs)

    def remember(self, obs, action, reward, next_obs, done):
        self.buffer.add(obs, action, reward, next_obs, done)
        self.steps += 1

    def learn(self) -> Optional[float]:
        if len(self.buffer) < max(self.batch_size, self.learn_start):
            return None
        obs, actions, rewards, next_obs, dones = self.buffer.sample(self.batch_size)
        q_taken = self.q(obs).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            # Double DQN: online net picks the next action, target net scores it (curbs overestimation).
            next_actions = self.q(next_obs).argmax(dim=1, keepdim=True)
            next_q = self.target(next_obs).gather(1, next_actions).squeeze(1)
            target = rewards + self.gamma * (1.0 - dones) * next_q
        loss = nn.functional.smooth_l1_loss(q_taken, target)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q.parameters(), 10.0)
        self.optimizer.step()
        self.updates += 1
        if self.updates % self.target_sync == 0:
            self.target.load_state_dict(self.q.state_dict())
        return float(loss.item())

    def checkpoint(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"state_dict": self.q.state_dict(), "obs_size": self.obs_size, "n_actions": self.n_actions,
                "hidden": self.hidden, "metadata": metadata}


def greedy_action(net: QNetwork, obs: np.ndarray) -> int:
    with torch.no_grad():
        return int(net(torch.from_numpy(obs).unsqueeze(0)).argmax(dim=1).item())


def load_q_network(path: str) -> tuple:
    ckpt = torch.load(path, map_location=DEVICE, weights_only=True)
    net = QNetwork(ckpt["obs_size"], ckpt["n_actions"], ckpt["hidden"])
    net.load_state_dict(ckpt["state_dict"])
    net.eval()
    return net, ckpt
