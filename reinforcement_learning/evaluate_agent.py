"""
reinforcement_learning/evaluate_agent.py
------------------------------------------
Phase 3d: Evaluation script for trained PPO and Q-learning agents.

Reports:
  - Average reward over N episodes
  - % unmet demand (energy satisfaction rate)
  - Average electricity cost per day
  - Peak grid load
  - Reward curve (saved as PNG)
  - Sample-day charging schedule (saved as PNG)

Usage:
    python -m reinforcement_learning.evaluate_agent
    python -m reinforcement_learning.evaluate_agent --model ppo --episodes 50
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving figs
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reinforcement_learning.environment import EVChargingEnv
from reinforcement_learning.dqn_model import load_ppo_agent, SAVED_MODELS_DIR
from reinforcement_learning.q_learning import TabularQAgent

# ─────────────────────────────────────────────
# Output directories
# ─────────────────────────────────────────────

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# Single-episode rollout
# ─────────────────────────────────────────────

def rollout(agent, env: EVChargingEnv, deterministic: bool = True) -> Dict:
    """Run one full episode. Returns a metrics dict."""
    obs, _ = env.reset()
    done    = False
    ep_reward = 0.0
    step_rewards   = []
    power_per_step = []

    while not done:
        if hasattr(agent, "predict"):
            action, _ = agent.predict(obs, deterministic=deterministic)
        else:
            action = agent.select_action(obs, deterministic=deterministic)

        obs, reward, terminated, truncated, info = env.step(action)
        ep_reward += reward
        step_rewards.append(reward)
        # Reconstruct total power from last power_history entry
        power_per_step.append(info.get("total_power_fraction", 0.0))
        done = terminated or truncated

    return {
        "ep_reward":       ep_reward,
        "ep_energy_kwh":   info["ep_energy_kwh"],
        "ep_cost_usd":     info["ep_cost_usd"],
        "ep_unmet_kwh":    info["ep_unmet_kwh"],
        "ep_overload_kwh": info["ep_overload_kwh"],
        "ep_rejected":     info["ep_rejected"],
        "ep_departures":   info["ep_departures"],
        "step_rewards":    step_rewards,
        "power_per_step":  power_per_step,
    }


# ─────────────────────────────────────────────
# Multi-episode evaluation
# ─────────────────────────────────────────────

def evaluate(
    agent,
    n_episodes: int = 50,
    seed: int = 99,
    agent_name: str = "Agent",
) -> Dict:
    env = EVChargingEnv(seed=seed)
    results = [rollout(agent, env) for _ in range(n_episodes)]
    env.close()

    rewards    = [r["ep_reward"]     for r in results]
    energies   = [r["ep_energy_kwh"] for r in results]
    costs      = [r["ep_cost_usd"]   for r in results]
    unmet      = [r["ep_unmet_kwh"]  for r in results]

    # Energy satisfaction rate: delivered / (delivered + unmet)
    sat_rates = [
        e / (e + u) if (e + u) > 0 else 1.0
        for e, u in zip(energies, unmet)
    ]

    summary = {
        "agent_name":        agent_name,
        "n_episodes":        n_episodes,
        "mean_reward":       float(np.mean(rewards)),
        "std_reward":        float(np.std(rewards)),
        "mean_energy_kwh":   float(np.mean(energies)),
        "mean_cost_usd":     float(np.mean(costs)),
        "mean_unmet_kwh":    float(np.mean(unmet)),
        "satisfaction_rate": float(np.mean(sat_rates)),
        "mean_rejected":     float(np.mean([r["ep_rejected"] for r in results])),
        "raw_results":       results,
    }
    return summary


# ─────────────────────────────────────────────
# Plotting helpers
# ─────────────────────────────────────────────

def plot_reward_comparison(ppo_summary: Dict, q_summary: Dict,
                            save_path: Path = RESULTS_DIR / "reward_comparison.png") -> None:
    """Bar chart comparing PPO vs Q-learning metrics."""
    labels  = ["Mean Reward", "Satisfaction %", "Mean Cost ($)"]
    ppo_vals = [
        ppo_summary["mean_reward"],
        ppo_summary["satisfaction_rate"] * 100,
        ppo_summary["mean_cost_usd"],
    ]
    q_vals = [
        q_summary["mean_reward"],
        q_summary["satisfaction_rate"] * 100,
        q_summary["mean_cost_usd"],
    ]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width/2, ppo_vals, width, label="PPO",      color="#4CAF50", alpha=0.85)
    bars2 = ax.bar(x + width/2, q_vals,   width, label="Q-Learning", color="#2196F3", alpha=0.85)

    ax.set_title("PPO vs Q-Learning: Key Metrics", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.bar_label(bars1, fmt="%.1f", padding=3)
    ax.bar_label(bars2, fmt="%.1f", padding=3)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved -> {save_path}")


def plot_sample_day(results: List[Dict],
                    save_path: Path = RESULTS_DIR / "sample_day.png") -> None:
    """Plot step rewards and power draw for a sample episode."""
    ep = results[0]  # first episode
    steps = range(1, len(ep["step_rewards"]) + 1)
    times = [s * 0.25 for s in steps]  # hours

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    # Step rewards
    ax1.plot(times, ep["step_rewards"], color="#E91E63", linewidth=1.5, alpha=0.9)
    ax1.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax1.fill_between(times, ep["step_rewards"], 0,
                     where=[r > 0 for r in ep["step_rewards"]],
                     color="green", alpha=0.2, label="Positive")
    ax1.fill_between(times, ep["step_rewards"], 0,
                     where=[r < 0 for r in ep["step_rewards"]],
                     color="red", alpha=0.2, label="Negative")
    ax1.set_ylabel("Step Reward", fontsize=11)
    ax1.set_title("Sample Day: Charging Schedule (PPO Agent)", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.3)

    # Power draw fraction
    ax2.plot(times, [p * 100 for p in ep["power_per_step"]],
             color="#2196F3", linewidth=1.5, alpha=0.9)
    ax2.axhline(100, color="red", linewidth=1, linestyle="--",
                label="Grid Capacity (100%)")
    ax2.set_ylabel("Grid Load (%)", fontsize=11)
    ax2.set_xlabel("Hour of Day", fontsize=11)
    ax2.set_ylim(0, 120)
    ax2.set_xticks(range(0, 25, 2))
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved -> {save_path}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main(model_type: str = "ppo", n_episodes: int = 50) -> None:
    print(f"\n=== EV Charging RL Evaluation ===")
    print(f"  Agent:    {model_type.upper()}")
    print(f"  Episodes: {n_episodes}\n")

    env = EVChargingEnv(seed=99)

    # Load PPO
    ppo_path = SAVED_MODELS_DIR / "best_model.zip"
    if not ppo_path.exists():
        ppo_path = SAVED_MODELS_DIR / "ppo_ev_final.zip"

    if ppo_path.exists():
        ppo_agent = load_ppo_agent(ppo_path, env=env)
        ppo_summary = evaluate(ppo_agent, n_episodes=n_episodes, agent_name="PPO")
        _print_summary(ppo_summary)
    else:
        print(f"  [WARNING] No trained PPO model found at {ppo_path}")
        print("  Run: python -m reinforcement_learning.train_agent first")
        return

    # Load Q-table (optional)
    q_path = SAVED_MODELS_DIR / "q_table.json"
    if q_path.exists():
        q_agent = TabularQAgent.load(q_path)
        q_summary = evaluate(q_agent, n_episodes=n_episodes, agent_name="Q-Learning")
        _print_summary(q_summary)
        plot_reward_comparison(ppo_summary, q_summary)
    else:
        print(f"  [INFO] No Q-table found at {q_path} — skipping Q-learning comparison")

    # Plots
    plot_sample_day(ppo_summary["raw_results"])
    print("\nEvaluation complete. Results saved to ./results/")


def _print_summary(s: Dict) -> None:
    print(f"\n  --- {s['agent_name']} ({s['n_episodes']} episodes) ---")
    print(f"    Mean reward:       {s['mean_reward']:.2f} +/- {s['std_reward']:.2f}")
    print(f"    Satisfaction rate: {s['satisfaction_rate']*100:.1f}%")
    print(f"    Mean cost/day:     ${s['mean_cost_usd']:.3f}")
    print(f"    Mean unmet kWh:    {s['mean_unmet_kwh']:.2f}")
    print(f"    Mean rejected EVs: {s['mean_rejected']:.1f}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Evaluate trained RL agents")
    parser.add_argument("--model",    choices=["ppo", "q"],  default="ppo")
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()
    main(model_type=args.model, n_episodes=args.episodes)
