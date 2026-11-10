import sys
import numpy as np
from pathlib import Path

# Resolve imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.app.rl.environment import EVSmartChargingEnv
from backend.app.rl.q_learning import QLearningAgent
from backend.app.rl.dqn_agent import DQNAgent

Q_TABLE_PATH = Path(__file__).resolve().parent / "saved_models" / "q_table.json"
DQN_MODEL_PATH = Path(__file__).resolve().parent / "saved_models" / "dqn_model.pth"

def train_q_learning(episodes=300):
    print("\n--- Training Tabular Q-Learning Agent ---")
    env = EVSmartChargingEnv()
    agent = QLearningAgent()
    rewards_history = []

    for ep in range(1, episodes + 1):
        state, _ = env.reset()
        ep_reward = 0
        done = False
        
        while not done:
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.update(state, action, reward, next_state, done)
            state = next_state
            ep_reward += reward

        agent.decay_epsilon()
        rewards_history.append(ep_reward)

        if ep % 50 == 0:
            print(f"Episode {ep}/{episodes} | Epsilon: {agent.epsilon:.3f} | Avg Reward: {np.mean(rewards_history[-50:]):.2f}")

    agent.save(Q_TABLE_PATH)
    return rewards_history


def train_dqn(episodes=150):
    print("\n--- Training Deep Q-Network Agent ---")
    env = EVSmartChargingEnv()
    agent = DQNAgent()
    rewards_history = []
    losses = []

    for ep in range(1, episodes + 1):
        state, _ = env.reset()
        ep_reward = 0
        done = False
        
        while not done:
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.memory.push(state, action, reward, next_state, done)
            state = next_state
            ep_reward += reward

            if len(agent.memory) > agent.batch_size:
                loss = agent.update()
                losses.append(loss)

        agent.decay_epsilon()
        rewards_history.append(ep_reward)

        if ep % 10 == 0:
            agent.update_target_network()

        if ep % 25 == 0:
            print(f"Episode {ep}/{episodes} | Epsilon: {agent.epsilon:.3f} | Avg Reward: {np.mean(rewards_history[-25:]):.2f}")

    agent.save(DQN_MODEL_PATH)
    return rewards_history


def train_all():
    q_rewards = train_q_learning(300)
    dqn_rewards = train_dqn(150)
    print("\nAll Reinforcement Learning agents trained successfully.")

if __name__ == "__main__":
    train_all()
