"""
Smoke test: run 96 random-action steps in the EVChargingEnv.
Verifies Phase 1 + Phase 2 integration works end-to-end.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from reinforcement_learning.environment import EVChargingEnv

print("=== EVChargingEnv Smoke Test ===\n")

env = EVChargingEnv(seed=42, render_mode=None)
obs, info = env.reset(seed=42)

print(f"Observation space: {env.observation_space}")
print(f"Action space:      {env.action_space}")
print(f"Obs shape:         {obs.shape}  | dtype: {obs.dtype}")
print(f"Obs range:         [{obs.min():.3f}, {obs.max():.3f}]")
print(f"Day type:          {'Weekend' if info['is_weekend'] else 'Weekday'}")
print()

total_reward    = 0.0
total_energy    = 0.0
total_arrivals  = 0
total_departures = 0
step_rewards    = []

for step in range(96):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    total_reward    += reward
    total_energy    += info.get("ep_energy_kwh", 0)
    total_arrivals  += info.get("arrivals", 0)
    step_rewards.append(reward)

    if step % 24 == 0 or step == 95:
        print(
            f"Step {step+1:3d}/96 | "
            f"Hour {info['hour']:02d}:00 | "
            f"Occupied {info['occupied_slots']}/{env.n_slots} | "
            f"Arrivals this step: {info['arrivals']} | "
            f"Step reward: {reward:.3f}"
        )

    if terminated:
        break

print()
print("=== Episode Summary ===")
print(f"  Total reward:       {info['ep_reward']:.3f}")
print(f"  Total energy kWh:   {info['ep_energy_kwh']:.2f}")
print(f"  Total cost USD:     ${info['ep_cost_usd']:.3f}")
print(f"  Unmet demand kWh:   {info['ep_unmet_kwh']:.2f}")
print(f"  Grid overload kWh:  {info['ep_overload_kwh']:.2f}")
print(f"  Rejected arrivals:  {info['ep_rejected']}")
print(f"  Completed sessions: {info['ep_departures']}")
print(f"  Mean step reward:   {np.mean(step_rewards):.4f}")
print(f"  Std step reward:    {np.std(step_rewards):.4f}")
print()
print("PASSED: env.step() ran 96 steps without error.")
