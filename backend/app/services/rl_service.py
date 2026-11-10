import os
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from backend.app.rl.q_learning import QLearningAgent
from backend.app.rl.dqn_agent import DQNAgent

_ROOT = Path(__file__).resolve().parent.parent
Q_TABLE_PATH = _ROOT / "rl" / "saved_models" / "q_table.json"
DQN_MODEL_PATH = _ROOT / "rl" / "saved_models" / "dqn_model.pth"

ACTIONS_MAP = {
    0: "CHARGE_NOW",
    1: "WAIT",
    2: "FAST_CHARGE",
    3: "SLOW_CHARGE",
    4: "CHANGE_STATION"
}

class RLService:
    def __init__(self):
        self.q_agent = QLearningAgent()
        self.dqn_agent = DQNAgent()
        self.q_loaded = False
        self.dqn_loaded = False
        self._load_agents()

    def _load_agents(self):
        try:
            if Q_TABLE_PATH.exists():
                self.q_loaded = self.q_agent.load(Q_TABLE_PATH)
            else:
                print(f"Warning: Q-table not found at {Q_TABLE_PATH}")

            if DQN_MODEL_PATH.exists():
                self.dqn_loaded = self.dqn_agent.load(DQN_MODEL_PATH)
            else:
                print(f"Warning: DQN weights not found at {DQN_MODEL_PATH}")
        except Exception as e:
            print(f"Error loading RL agents: {e}")

    def get_recommendation(
        self,
        soc: float,
        soh: float,
        temperature: float,
        price: float,
        queue_length: int,
        charger_availability: int,
        distance: float,
        charging_demand: float,
        agent_type: str = "DQN"
    ) -> Dict[str, Any]:
        """
        Evaluate inputs and return optimal charging recommendation from Q-learning or DQN agent.
        """
        # Convert inputs to state vector
        # State: [SOC, SOH, Temp, Price, Queue, Availability, Distance, Demand]
        state = np.array([
            soc / 100.0 if soc > 1.0 else soc,
            soh / 100.0 if soh > 1.0 else soh,
            temperature,
            price,
            float(queue_length),
            float(charger_availability),
            distance,
            charging_demand
        ], dtype=np.float32)

        action_idx = 1 # Default: WAIT
        confidence = 0.5
        q_values_out = [0.0] * 5

        # Query selected model
        if agent_type == "Q-LEARNING" and self.q_loaded:
            action_idx = self.q_agent.select_action(state, deterministic=True)
            state_key = self.q_agent._discretize(state)
            q_values = self.q_agent._get_q_values(state_key)
            q_values_out = q_values.tolist()
            # Calculate confidence using softmax over Q-values
            exp_q = np.exp(q_values - np.max(q_values))
            probs = exp_q / np.sum(exp_q)
            confidence = float(probs[action_idx])
            
        elif self.dqn_loaded: # Default to DQN
            action_idx = self.dqn_agent.select_action(state, deterministic=True)
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.dqn_agent.device)
            with torch.no_grad():
                q_vals = self.dqn_agent.policy_net(state_t).cpu().numpy()[0]
                q_values_out = q_vals.tolist()
                exp_q = np.exp(q_vals - np.max(q_vals))
                probs = exp_q / np.sum(exp_q)
                confidence = float(probs[action_idx])
        else:
            # Heuristic fallback if models not loaded
            if soc < 0.2:
                action_idx = 2 if charger_availability > 0 else 4
            elif price > 12.0:
                action_idx = 1
            else:
                action_idx = 3

        action_str = ACTIONS_MAP[action_idx]

        # Calculate estimated cost and wait time based on chosen action
        est_cost = 0.0
        est_wait = 0
        reasons = []

        # Formulate reasoning explanations and parameters
        if action_idx == 0: # Charge Now
            est_cost = 0.15 * charging_demand * price
            est_wait = queue_length * 5
            reasons.append("Moderate charging cost and acceptable waiting queue.")
            if charger_availability > 2:
                reasons.append("High charger slot availability detected.")
                
        elif action_idx == 1: # Wait
            est_cost = 0.0
            est_wait = 15
            reasons.append("Electricity price is currently peak; waiting for tariff drop.")
            if temperature > 40.0:
                reasons.append("Battery temperature is elevated. Waiting allows cooling.")

        elif action_idx == 2: # Fast Charge
            est_cost = 0.40 * charging_demand * price * 1.3
            est_wait = queue_length * 3
            reasons.append("Low state of charge (SoC) requires urgent power dispatch.")
            if temperature < 35.0:
                reasons.append("Battery temperature is safe for high-power thermal loading.")

        elif action_idx == 3: # Slow Charge
            est_cost = 0.07 * charging_demand * price * 0.9
            est_wait = queue_length * 10
            reasons.append("Low tariff price and healthy battery preservation charging rate.")
            if soh < 0.85:
                reasons.append("Degraded state of health requires battery-friendly low-amp charging.")

        elif action_idx == 4: # Change Station
            est_cost = distance * 1.5
            est_wait = int(distance * 4)
            reasons.append("Current station is congested or lacks available chargers.")
            if price > 13.0:
                reasons.append("Tariff rates at this station are significantly inflated.")

        # Estimate reward score
        reward_est = float(np.max(q_values_out)) if max(q_values_out) != 0.0 else 5.0

        return {
            "action": action_str,
            "station": "Station Alpha" if action_idx != 4 else "Find Alternative Hub",
            "estimated_cost": round(est_cost, 2),
            "estimated_wait": est_wait,
            "reward": round(reward_est, 2),
            "confidence": round(confidence, 2),
            "reason": reasons,
            "q_values": q_values_out
        }

# Instantiate global service
rl_service = RLService()
