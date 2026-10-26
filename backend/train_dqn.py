"""Offline DQN training. The API never trains; it only loads the weights written here.

    python train_dqn.py                 # train on seeds 0-99, write models/dqn.pt and models/dqn_rewards.csv
    python train_dqn.py --epochs 2      # quicker run
    python train_dqn.py --eval          # evaluate every policy on held-out seeds 1000+ (no training)
"""
import argparse
import copy
import csv
import os
import time
from datetime import datetime, timezone

import numpy as np
import torch

from evaluation import EVAL_SEED_START, eval_seeds, format_table, summarize
from rl.dqn_agent import DQNAgent
from rl.env import DataCenterEnv, env_signature

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_SEEDS = list(range(0, 100))
VALIDATION_SEEDS = list(range(100, 105))  # checkpoint selection only; never trained on, never reported
assert max(TRAIN_SEEDS) < min(VALIDATION_SEEDS) and max(VALIDATION_SEEDS) < EVAL_SEED_START, \
    "training, validation and held-out evaluation seeds must not overlap"


def greedy_return(agent: DQNAgent, env: DataCenterEnv, seeds) -> float:
    total = 0.0
    for s in seeds:
        obs, done = env.reset(s), False
        while not done:
            obs, reward, done, _ = env.step(agent.act(obs, greedy=True))
            total += reward
    return total / len(seeds)


def train(epochs: int, num_tasks: int, out_path: str, log_path: str, seed: int, sleep_enabled: bool = True):
    torch.set_num_threads(1)
    env = DataCenterEnv(num_tasks=num_tasks, sleep_enabled=sleep_enabled)
    total_steps = epochs * len(TRAIN_SEEDS) * num_tasks
    agent = DQNAgent(env.obs_size, env.n_actions, eps_decay_steps=int(0.6 * total_steps), seed=seed)
    rng = np.random.default_rng(seed)

    val_env = DataCenterEnv(num_tasks=num_tasks, sleep_enabled=sleep_enabled)
    best_val, best_epoch, best_state = float("-inf"), 0, copy.deepcopy(agent.q.state_dict())

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    started = time.time()
    episode = 0
    with open(log_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["episode", "epoch", "seed", "epsilon", "reward", "energy_kwh", "sla_violations",
                         "overload", "mean_loss"])
        for epoch in range(1, epochs + 1):
            epoch_rewards = []
            for train_seed in rng.permutation(TRAIN_SEEDS):
                obs, done, total, losses = env.reset(int(train_seed)), False, 0.0, []
                while not done:
                    action = agent.act(obs)
                    next_obs, reward, done, _ = env.step(action)
                    agent.remember(obs, action, reward, next_obs, done)
                    loss = agent.learn()
                    if loss is not None:
                        losses.append(loss)
                    obs, total = next_obs, total + reward
                episode += 1
                epoch_rewards.append(total)
                writer.writerow([episode, epoch, int(train_seed), round(agent.epsilon, 4), round(total, 4),
                                 round(env.dc.energy_j / 3.6e6, 6), env.dc.violations,
                                 round(env.dc.overload_excess, 4), round(float(np.mean(losses)), 6) if losses else ""])
            fh.flush()
            val = greedy_return(agent, val_env, VALIDATION_SEEDS)
            marker = ""
            if val > best_val:
                best_val, best_epoch = val, epoch
                best_state = copy.deepcopy(agent.q.state_dict())
                marker = "  <- best"
            print(f"epoch {epoch}/{epochs}  mean train reward {np.mean(epoch_rewards):9.3f}  "
                  f"greedy val reward {val:9.3f}  epsilon {agent.epsilon:.3f}  "
                  f"elapsed {time.time() - started:6.1f}s{marker}", flush=True)

    agent.q.load_state_dict(best_state)
    metadata = {
        "env_signature": env_signature(),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train_seeds": [TRAIN_SEEDS[0], TRAIN_SEEDS[-1]],
        "epochs": epochs,
        "best_epoch": best_epoch,
        "validation_seeds": [VALIDATION_SEEDS[0], VALIDATION_SEEDS[-1]],
        "validation_reward": best_val,
        "num_tasks": num_tasks,
        "sleep_enabled": sleep_enabled,
        "seed": seed,
    }
    torch.save(agent.checkpoint(metadata), out_path)
    print(f"saved weights (epoch {best_epoch}) -> {out_path}\nreward log    -> {log_path}")


def evaluate(n_seeds: int, num_tasks: int):
    from database import INITIAL_16_SERVERS
    from policies import POLICY_NAMES, PolicyUnavailable, get_policy
    from simulation import run_simulation

    seeds = eval_seeds(n_seeds)
    runs = {}
    for name in POLICY_NAMES:
        try:
            policy = get_policy(name)
        except PolicyUnavailable as exc:
            print(f"skipping {name}: {exc}")
            continue
        runs[name] = [run_simulation(INITIAL_16_SERVERS, policy, num_tasks=num_tasks, seed=s) for s in seeds]
    print(f"held-out seeds {seeds[0]}-{seeds[-1]}, {num_tasks} tasks, sleep on")
    print(format_table(summarize(runs)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--epochs", type=int, default=6, help="passes over the 100 training seeds")
    parser.add_argument("--num-tasks", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0, help="seed for network init and exploration")
    parser.add_argument("--out", default=os.path.join(HERE, "models", "dqn.pt"))
    parser.add_argument("--log", default=os.path.join(HERE, "models", "dqn_rewards.csv"))
    parser.add_argument("--eval", action="store_true", help="evaluate saved weights on held-out seeds, no training")
    parser.add_argument("--eval-seeds", type=int, default=10)
    args = parser.parse_args()
    if args.eval:
        evaluate(args.eval_seeds, args.num_tasks)
    else:
        train(args.epochs, args.num_tasks, args.out, args.log, args.seed)


if __name__ == "__main__":
    main()
