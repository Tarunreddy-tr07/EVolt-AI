"""
reinforcement_learning/train_agent.py
---------------------------------------
Phase 3c: Training script for the PPO agent.

Trains for N total timesteps, saves checkpoints every 50k steps,
and runs a final evaluation at the end.

Usage:
    python -m reinforcement_learning.train_agent
    python -m reinforcement_learning.train_agent --timesteps 100000 --seed 42
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import (
    EvalCallback, CheckpointCallback, CallbackList,
)

from reinforcement_learning.environment import EVChargingEnv
from reinforcement_learning.dqn_model import make_ppo_agent, SAVED_MODELS_DIR

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

CHECKPOINT_DIR  = SAVED_MODELS_DIR / "checkpoints"
BEST_MODEL_PATH = SAVED_MODELS_DIR / "ppo_ev_best"
FINAL_MODEL_PATH = SAVED_MODELS_DIR / "ppo_ev_final"
LOG_DIR         = Path("logs") / "ppo_tb"


# ─────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────

def train(
    total_timesteps: int = 500_000,
    seed: int = 0,
    checkpoint_freq: int = 50_000,
    eval_freq: int = 10_000,
    n_eval_episodes: int = 10,
    verbose: int = 1,
) -> None:
    """End-to-end PPO training + checkpointing."""

    # Create directories
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Training environment
    train_env = Monitor(EVChargingEnv(seed=seed))

    # Evaluation environment (fixed seed for reproducibility)
    eval_env = Monitor(EVChargingEnv(seed=seed + 1, fixed_day_of_week=2))

    # Build agent
    agent = make_ppo_agent(
        env=train_env,
        seed=seed,
        n_steps=512,             # shorter rollout for faster iteration
        batch_size=64,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.95,
        clip_range=0.2,
        net_arch=[256, 256],     # wider than default for our 27-dim obs
        tensorboard_log=str(LOG_DIR),
        verbose=verbose,
    )

    # Callbacks
    checkpoint_cb = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=str(CHECKPOINT_DIR),
        name_prefix="ppo_ev",
        verbose=1,
    )
    eval_cb = EvalCallback(
        eval_env=eval_env,
        best_model_save_path=str(SAVED_MODELS_DIR),
        log_path=str(LOG_DIR),
        eval_freq=eval_freq,
        n_eval_episodes=n_eval_episodes,
        deterministic=True,
        verbose=1,
    )
    callbacks = CallbackList([checkpoint_cb, eval_cb])

    print(f"\n=== PPO Training ===")
    print(f"  Timesteps:      {total_timesteps:,}")
    print(f"  Checkpoint dir: {CHECKPOINT_DIR}")
    print(f"  Best model:     {BEST_MODEL_PATH}")
    print(f"  TensorBoard:    tensorboard --logdir {LOG_DIR}")
    print()

    agent.learn(
        total_timesteps=total_timesteps,
        callback=callbacks,
        progress_bar=True,
        reset_num_timesteps=True,
    )

    # Save final model
    agent.save(str(FINAL_MODEL_PATH))
    print(f"\nFinal model saved -> {FINAL_MODEL_PATH}.zip")

    train_env.close()
    eval_env.close()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Train PPO agent for EV charging")
    parser.add_argument("--timesteps", type=int, default=500_000,
                        help="Total training timesteps (default: 500,000)")
    parser.add_argument("--seed",      type=int, default=0)
    parser.add_argument("--checkpoint-freq", type=int, default=50_000)
    parser.add_argument("--eval-freq",       type=int, default=10_000)
    parser.add_argument("--n-eval-episodes", type=int, default=10)
    parser.add_argument("--quiet", action="store_true",
                        help="Reduce verbosity")
    args = parser.parse_args()

    train(
        total_timesteps=args.timesteps,
        seed=args.seed,
        checkpoint_freq=args.checkpoint_freq,
        eval_freq=args.eval_freq,
        n_eval_episodes=args.n_eval_episodes,
        verbose=0 if args.quiet else 1,
    )
