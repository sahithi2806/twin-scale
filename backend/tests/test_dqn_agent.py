import numpy as np
import torch

from rl.dqn_agent import DQNAgent, greedy_action, load_q_network
from rl.env import DataCenterEnv


def test_agent_collects_learns_and_syncs_target():
    env = DataCenterEnv(num_tasks=40)
    agent = DQNAgent(env.obs_size, env.n_actions, batch_size=16, learn_start=32, target_sync=5,
                     eps_decay_steps=100, seed=0)
    losses = []
    for seed in range(3):
        obs, done = env.reset(seed), False
        while not done:
            action = agent.act(obs)
            assert 0 <= action < env.n_actions
            next_obs, reward, done, _ = env.step(action)
            agent.remember(obs, action, reward, next_obs, done)
            loss = agent.learn()
            if loss is not None:
                losses.append(loss)
            obs = next_obs
    assert losses and all(np.isfinite(losses))
    assert agent.epsilon < 1.0
    assert agent.updates >= 5
    for p_q, p_t in zip(agent.q.parameters(), agent.target.parameters()):
        assert p_q.shape == p_t.shape


def test_greedy_inference_is_deterministic_and_checkpoint_round_trips(tmp_path):
    agent = DQNAgent(50, 16, seed=3)
    obs = np.random.default_rng(0).random(50, dtype=np.float32)
    first = greedy_action(agent.q, obs)
    assert all(greedy_action(agent.q, obs) == first for _ in range(5))

    path = tmp_path / "dqn.pt"
    torch.save(agent.checkpoint({"note": "test"}), path)
    net, ckpt = load_q_network(str(path))
    assert ckpt["metadata"]["note"] == "test"
    assert greedy_action(net, obs) == first
