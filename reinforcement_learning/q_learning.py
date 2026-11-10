"""
reinforcement_learning/q_learning.py
--------------------------------------
Phase 3a: Tabular Q-Learning baseline for the EVChargingEnv.

Because the full state space is continuous, we discretise each of the
27 observation dimensions into N_BINS bins and use a flat numpy array
as the Q-table.  Due to the exponential table size this is only practical
as a proof-of-concept / baseline comparison for the report.

Usage:
    python -m reinforcement_learning.q_learning --episodes 500 --eval 50
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reinforcement_learning.environment import EVChargingEnv
from reinforcement_learning.action_space import N_RATE_LEVELS
from reinforcement_learning.state_space import N_SLOTS

# ─────────────────────────────────────────────
# Discretisation
# ─────────────────────────────────────────────

N_BINS = 5           # bins per continuous obs dimension
OBS_DIM = N_SLOTS * 4 + 3  # 27

# Use only a REDUCED state (key dimensions) to keep table small:
#   per-slot: occupied (binary), soc (5 bins), time_remaining (5 bins)
#   global:   hour (24 buckets), tou_price (3 levels)
#
# Reduced state dims = N_SLOTS * 3 + 2 = 20
# Q-table shape: (2, 5, 5)^N_SLOTS × 24 × 3 × 5^N_SLOTS
# This is still large; in practice we use a dict-based Q-table.

class TabularQAgent:
    """
    Dictionary-backed tabular Q-learning agent.

    State key = tuple of discretised observations.
    Action = tuple of per-slot rate indices.
    """

    def __init__(
        self,
        n_slots: int = N_SLOTS,
        n_rate_levels: int = N_RATE_LEVELS,
        alpha: float = 0.1,     # learning rate
        gamma: float = 0.95,    # discount factor
        epsilon: float = 1.0,   # initial exploration rate
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        n_bins: int = N_BINS,
    ):
        self.n_slots       = n_slots
        self.n_rate_levels = n_rate_levels
        self.alpha         = alpha
        self.gamma         = gamma
        self.epsilon       = epsilon
        self.epsilon_min   = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.n_bins        = n_bins

        # Dict Q-table: state_key -> np.ndarray shape (n_rate_levels^n_slots,)
        # We flatten the MultiDiscrete action to a single integer index
        self.q_table: dict = {}
        self._n_actions = n_rate_levels ** n_slots

        # Bin edges for each observation dimension (0..1 range)
        self._bins = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]  # interior edges

    # ── State discretisation ─────────────────────────────────────────────

    def _discretise(self, obs: np.ndarray) -> tuple:
        """Convert continuous obs to a hashable discrete state key."""
        return tuple(np.digitize(obs, self._bins).tolist())

    # ── Action helpers ───────────────────────────────────────────────────

    def _flatten_action(self, action: np.ndarray) -> int:
        """MultiDiscrete action array -> single integer index."""
        idx = 0
        for a in action:
            idx = idx * self.n_rate_levels + int(a)
        return idx

    def _unflatten_action(self, idx: int) -> np.ndarray:
        """Single integer index -> MultiDiscrete action array."""
        action = []
        for _ in range(self.n_slots):
            action.append(idx % self.n_rate_levels)
            idx //= self.n_rate_levels
        return np.array(action[::-1], dtype=int)

    def _get_q(self, state_key: tuple) -> np.ndarray:
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self._n_actions, dtype=np.float32)
        return self.q_table[state_key]

    # ── Policy ───────────────────────────────────────────────────────────

    def select_action(self, obs: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """Epsilon-greedy action selection."""
        if not deterministic and np.random.random() < self.epsilon:
            return np.random.randint(0, self.n_rate_levels, size=self.n_slots)
        state_key = self._discretise(obs)
        q_vals = self._get_q(state_key)
        best_idx = int(np.argmax(q_vals))
        return self._unflatten_action(best_idx)

    # ── Update ───────────────────────────────────────────────────────────

    def update(
        self,
        obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_obs: np.ndarray,
        done: bool,
    ) -> float:
        """One Q-learning update step. Returns TD error."""
        s  = self._discretise(obs)
        s_ = self._discretise(next_obs)
        a_idx  = self._flatten_action(action)

        q_s  = self._get_q(s)
        q_s_ = self._get_q(s_)

        td_target = reward + (0.0 if done else self.gamma * float(np.max(q_s_)))
        td_error  = td_target - q_s[a_idx]
        q_s[a_idx] += self.alpha * td_error
        return float(td_error)

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    @property
    def n_states_visited(self) -> int:
        return len(self.q_table)

    def save(self, path: Path) -> None:
        """Save Q-table to a JSON-serialisable dict."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        serialisable = {
            str(k): v.tolist()
            for k, v in self.q_table.items()
        }
        meta = {
            "n_slots":       self.n_slots,
            "n_rate_levels": self.n_rate_levels,
            "alpha":         self.alpha,
            "gamma":         self.gamma,
            "epsilon":       self.epsilon,
            "epsilon_min":   self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "n_bins":        self.n_bins,
            "n_states":      self.n_states_visited,
        }
        with open(path, "w") as f:
            json.dump({"meta": meta, "q_table": serialisable}, f)
        print(f"Q-table saved -> {path}  ({self.n_states_visited} states)")

    @classmethod
    def load(cls, path: Path) -> "TabularQAgent":
        with open(path, "r") as f:
            data = json.load(f)
        meta = data["meta"]
        agent = cls(
            n_slots=meta["n_slots"],
            n_rate_levels=meta["n_rate_levels"],
            alpha=meta["alpha"],
            gamma=meta["gamma"],
            epsilon=meta["epsilon"],
            epsilon_min=meta["epsilon_min"],
            epsilon_decay=meta["epsilon_decay"],
            n_bins=meta["n_bins"],
        )
        agent.q_table = {
            eval(k): np.array(v, dtype=np.float32)
            for k, v in data["q_table"].items()
        }
        return agent


# ─────────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────────

def train(
    n_episodes: int = 500,
    eval_every: int = 50,
    seed: int = 0,
    save_path: Path = Path("reinforcement_learning/saved_models/q_table.json"),
) -> Tuple[TabularQAgent, List[float]]:
    """Train the tabular Q-agent and return (agent, episode_rewards)."""
    env   = EVChargingEnv(seed=seed)
    agent = TabularQAgent()
    ep_rewards = []

    print(f"Training Q-agent for {n_episodes} episodes...")
    for ep in range(1, n_episodes + 1):
        obs, _ = env.reset()
        ep_reward = 0.0
        done = False

        while not done:
            action = agent.select_action(obs)
            next_obs, reward, terminated, truncated, _ = env.step(action)
            agent.update(obs, action, reward, next_obs, terminated or truncated)
            obs = next_obs
            ep_reward += reward
            done = terminated or truncated

        agent.decay_epsilon()
        ep_rewards.append(ep_reward)

        if ep % eval_every == 0:
            # Quick greedy eval over 5 episodes
            eval_rewards = []
            for _ in range(5):
                o, _ = env.reset()
                r_sum = 0.0
                d = False
                while not d:
                    a = agent.select_action(o, deterministic=True)
                    o, r, t, tr, _ = env.step(a)
                    r_sum += r
                    d = t or tr
                eval_rewards.append(r_sum)
            print(
                f"  Ep {ep:4d}/{n_episodes} | "
                f"train_r={ep_reward:.1f} | "
                f"eval_r={sum(eval_rewards)/len(eval_rewards):.1f} | "
                f"eps={agent.epsilon:.3f} | "
                f"states={agent.n_states_visited}"
            )

    agent.save(save_path)
    return agent, ep_rewards


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Train tabular Q-learning baseline")
    parser.add_argument("--episodes", type=int, default=500)
    parser.add_argument("--eval",     type=int, default=50,
                        help="Evaluate every N episodes")
    parser.add_argument("--seed",     type=int, default=0)
    parser.add_argument("--save",     type=str,
                        default="reinforcement_learning/saved_models/q_table.json")
    args = parser.parse_args()

    agent, rewards = train(
        n_episodes=args.episodes,
        eval_every=args.eval,
        seed=args.seed,
        save_path=Path(args.save),
    )
    print(f"\nFinal 10-episode avg reward: {sum(rewards[-10:])/10:.2f}")
