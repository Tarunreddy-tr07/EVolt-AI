import json
import numpy as np
from pathlib import Path

class QLearningAgent:
    def __init__(
        self,
        action_dim: int = 5,
        alpha: float = 0.1,    # learning rate
        gamma: float = 0.95,   # discount factor
        epsilon: float = 1.0,  # exploration rate
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995
    ):
        self.action_dim = action_dim
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table = {}

    def _discretize(self, state: np.ndarray) -> tuple:
        """Discretize continuous state (8 variables) to a hashable state key tuple."""
        soc, soh, temp, price, queue, availability, distance, demand = state
        
        # SOC bins (5)
        soc_bin = int(np.clip(soc * 5, 0, 4))
        # SOH bins (2)
        soh_bin = 0 if soh < 0.85 else 1
        # Temperature bins (3)
        temp_bin = 0 if temp < 35.0 else (1 if temp < 45.0 else 2)
        # Price bins (3)
        price_bin = 0 if price < 8.0 else (1 if price < 12.0 else 2)
        # Queue bins (3)
        queue_bin = 0 if queue < 1 else (1 if queue < 4 else 2)
        # Availability bins (2)
        avail_bin = 0 if availability == 0 else 1
        # Distance bins (2)
        dist_bin = 0 if distance < 3.0 else 1
        # Demand bins (2)
        demand_bin = 0 if demand < 40.0 else 1

        return (soc_bin, soh_bin, temp_bin, price_bin, queue_bin, avail_bin, dist_bin, demand_bin)

    def _get_q_values(self, state_key: tuple) -> np.ndarray:
        if state_key not in self.q_table:
            # Initialize with small random values to break ties
            self.q_table[state_key] = np.random.uniform(-0.01, 0.01, size=self.action_dim).tolist()
        return np.array(self.q_table[state_key])

    def select_action(self, state: np.ndarray, deterministic: bool = False) -> int:
        state_key = self._discretize(state)
        
        # Epsilon-greedy
        if not deterministic and np.random.random() < self.epsilon:
            return int(np.random.randint(0, self.action_dim))
        
        q_values = self._get_q_values(state_key)
        return int(np.argmax(q_values))

    def update(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        s_key = self._discretize(state)
        ns_key = self._discretize(next_state)
        
        q_values = self._get_q_values(s_key)
        next_q_values = self._get_q_values(ns_key)
        
        target = reward
        if not done:
            target += self.gamma * np.max(next_q_values)
            
        td_error = target - q_values[action]
        q_values[action] += self.alpha * td_error
        
        # Save updated list back
        self.q_table[s_key] = q_values.tolist()
        return td_error

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert state keys (tuples) to strings for JSON compatibility
        serializable_table = {str(k): v for k, v in self.q_table.items()}
        data = {
            "meta": {
                "epsilon": self.epsilon,
                "alpha": self.alpha,
                "gamma": self.gamma
            },
            "q_table": serializable_table
        }
        with open(path, "w") as f:
            json.dump(data, f)
        print(f"Q-table saved -> {path} ({len(self.q_table)} states)")

    def load(self, path: Path):
        path = Path(path)
        if not path.exists():
            print(f"Warning: Q-table file not found at {path}. Starting fresh.")
            return False
            
        with open(path, "r") as f:
            data = json.load(f)
            
        self.epsilon = data["meta"]["epsilon"]
        self.alpha = data["meta"]["alpha"]
        self.gamma = data["meta"]["gamma"]
        
        # Reconstruct tuples from string keys
        self.q_table = {eval(k): v for k, v in data["q_table"].items()}
        print(f"Q-table loaded -> {path} ({len(self.q_table)} states)")
        return True
