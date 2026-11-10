"""
reinforcement_learning/dqn_model.py
-------------------------------------
Phase 3b: PPO agent using Stable-Baselines3.

PPO is chosen over DQN because:
  - Gymnasium MultiDiscrete action spaces are natively supported.
  - More stable training with clipped policy gradients.
  - SB3's MlpPolicy handles the flat obs vector out-of-the-box.

This module exposes:
  - make_ppo_agent()   : creates a configured SB3 PPO instance
  - load_ppo_agent()   : loads a saved model from disk
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
from stable_baselines3.common.callbacks import (
    EvalCallback, CheckpointCallback, CallbackList,
)
from stable_baselines3.common.monitor import Monitor

from reinforcement_learning.environment import EVChargingEnv

# ─────────────────────────────────────────────
# Model directories
# ─────────────────────────────────────────────

SAVED_MODELS_DIR = Path(__file__).parent / "saved_models"
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# PPO factory
# ─────────────────────────────────────────────

def make_ppo_agent(
    env=None,
    seed: int = 0,
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.95,
    clip_range: float = 0.2,
    net_arch: list = None,
    tensorboard_log: Optional[str] = "./logs/ppo_tb",
    verbose: int = 1,
) -> PPO:
    """
    Create and configure a Stable-Baselines3 PPO agent.

    Parameters
    ----------
    env : gymnasium Env or VecEnv
        If None, a default EVChargingEnv is created.
    net_arch : list
        Hidden layer sizes. Default: [128, 128] (policy & value nets).
    """
    if env is None:
        env = Monitor(EVChargingEnv(seed=seed))

    if net_arch is None:
        net_arch = [128, 128]

    policy_kwargs = {"net_arch": net_arch}

    agent = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        clip_range=clip_range,
        policy_kwargs=policy_kwargs,
        tensorboard_log=tensorboard_log,
        verbose=verbose,
        seed=seed,
    )
    return agent


def load_ppo_agent(model_path: Path, env=None) -> PPO:
    """
    Load a saved PPO model.

    Parameters
    ----------
    model_path : Path   Path to the .zip file saved by PPO.save().
    env        : Gym env (optional, for continued training).
    """
    if env is None:
        env = Monitor(EVChargingEnv())

    model = PPO.load(str(model_path), env=env)
    print(f"Loaded PPO model from {model_path}")
    return model
