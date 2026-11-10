# EVolt Charging & Battery Management System (RL Engine)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

An AI-driven Smart Grid Scheduling and Battery Health Telemetry platform built as a **B.Tech Artificial Intelligence & Data Science project**.

The system leverages **Deep Reinforcement Learning (DQN & Tabular Q-Learning)** to optimize EV charging profiles, balance local substation transformer loads, minimize consumer tariffs, and mitigate battery thermal degradation.

## Frontend Theme

The interface uses a light, digital-technology-inspired design: a soft blue-white background with subtle circuit-grid detailing, blue highlights for navigation and primary actions, and orange energy accents. Cards use translucent white surfaces, and maps retain their standard light tiles for readability.

---

## 1. System Architecture

```
                   +-------------------------------------------------+
                   |           React 19 Frontend SPA (Vite)          |
                   |   (Interactive Dashboard, RL Sandbox, Map Hub)  |
                   +------------------------+------------------------+
                                            |
                                            | REST API (JWT Authenticated)
                                            v
                   +-------------------------------------------------+
                   |              FastAPI ASGI Server                |
                   |        (Modular Routers & Service Layer)        |
                   +----+-------------------+-------------------+----+
                        |                   |                   |
                        v                   v                   v
             +--------------------+ +---------------+ +--------------------+
             |   SQLite Database  | |   ML Models   | |     RL Engine      |
             |  (ev_charging.db)  | |  (Random      | |  (Gymnasium Env +  |
             |   SQLAlchemy ORM   | |   Forest/GB)  | |   DQN / Q-Learning)|
             +--------------------+ +---------------+ +--------------------+
```

---

## 2. Directory Structure

```text
electric_charge/
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── database.py              # SQLAlchemy database engine & session
│       ├── main.py                  # FastAPI application entrypoint & analytics
│       ├── seed.py                  # Database seeder (stations, users, telemetry)
│       ├── models/
│       │   └── models.py            # ORM entities (User, Vehicle, Station, Session, etc.)
│       ├── routers/                 # Modular API endpoints
│       │   ├── auth.py              # User registration, login, and JWT decoding
│       │   ├── battery.py           # Battery telemetry, SoC & SoH prediction
│       │   ├── bookings.py          # Slot reservations & queue management
│       │   ├── rl_controller.py     # RL recommendation queries & simulation
│       │   ├── stations.py          # Station locator & charger listings
│       │   └── vehicles.py          # EV profiles & vehicle management
│       ├── services/                # Business logic & inference engines
│       │   ├── ml_service.py        # SoC & SoH machine learning models
│       │   └── rl_service.py        # DQN & Q-Learning recommendation engine
│       ├── rl/                      # Reinforcement learning components
│       │   ├── dqn_agent.py         # PyTorch Deep Q-Network agent
│       │   ├── environment.py       # Custom Gymnasium EV charging environment
│       │   ├── q_learning.py        # Tabular Q-Learning agent
│       │   ├── train_agents.py      # RL training pipeline
│       │   └── saved_models/        # Serialized weights (dqn_model.pth, q_table.json)
│       ├── schemas/                 # Pydantic validation schemas
│       └── utils/                   # Security, password hashing & JWT helpers
├── frontend/                        # React 19 + TypeScript + Vite SPA
│   ├── src/
│   │   ├── pages/                   # Views: Dashboard, SmartCharging, Battery, Map, etc.
│   │   ├── layouts/                 # Dashboard layout & navigation
│   │   ├── services/api.ts          # Axios client with JWT interceptor
│   │   └── App.tsx                  # Client-side router & route guard
│   ├── package.json
│   └── vite.config.ts
├── machine_learning/                # Battery degradation training & models
│   └── saved_models/                # soc_model.joblib & soh_model.joblib
├── reinforcement_learning/          # Research & baseline training scripts
├── data/                            # Datasets & arrival distributions
├── ev_charging.db                   # SQLite runtime database
├── backend.Dockerfile               # FastAPI container specification
├── docker-compose.yml               # Multi-container orchestration
├── start.bat                        # Windows concurrent start script
└── requirements.txt                 # Python dependencies
```

---

## 3. Reinforcement Learning Formulation

The decision problem is modeled as a **Markov Decision Process (MDP)** answering:
> *"Given the battery health, grid tariffs, and station demand, what is the optimal charging action?"*

### State Space $S \in \mathbb{R}^8$ (Continuous)
| Feature | Range | Description |
| :--- | :--- | :--- |
| **SOC** | $0.0 - 1.0$ | Battery State of Charge |
| **SOH** | $0.6 - 1.0$ | Battery State of Health |
| **Temperature** | $15^\circ\text{C} - 60^\circ\text{C}$ | Current battery pack temperature |
| **Tariff Price** | $5.0 - 15.0$ ₹/kWh | Real-time electricity cost |
| **Queue Length** | $0 - 10$ | Vehicles queued at station |
| **Availability** | $0 - 10$ | Free charging ports |
| **Distance** | $0.1 - 10.0$ km | Distance to charging station |
| **Demand** | $10.0 - 100.0$ kWh | Requested charging energy |

### Action Space $A \in \{0, 1, 2, 3, 4\}$ (Discrete)
- **0 (Charge Now)**: Standard AC/DC charging at nominal rate.
- **1 (Wait)**: Defer charging; allows battery cooldown and avoids peak pricing.
- **2 (Fast Charge)**: High-power DC charging ($50\text{ kW}$); higher speed, but adds thermal and degradation penalties.
- **3 (Slow Charge)**: Eco-friendly AC charging ($7.4\text{ kW}$); preserves battery lifespan and minimizes tariffs.
- **4 (Change Station)**: Re-routes vehicle to an alternate hub if current hub is full or queue is long.

### Reward Function
$$R = w_1 \cdot \text{Success} - w_2 \cdot \text{Cost} - w_3 \cdot \text{WaitTime} - w_4 \cdot \text{Degradation} - w_5 \cdot \text{TempPenalty} - w_6 \cdot \text{OverloadPenalty}$$

---

## 4. Machine Learning & Telemetry

Managed by `backend.app.services.ml_service`:
* **State of Charge (SoC)**: Random Forest regressor inferring battery charge percentage based on voltage, current, duration, and delivered power.
* **State of Health (SoH)**: Gradient Boosting regressor predicting battery capacity fade and estimating **Remaining Useful Life (RUL)** in cycles and years.

---

## 5. Quickstart & Local Execution

### Prerequisites
* **Python**: v3.10+ (tested with Python 3.12)
* **Node.js**: v18+ (tested with Node.js v24)
* **npm**: v9+

### Option A: One-Command Startup (Windows)
In **PowerShell**, run:
```powershell
.\start.bat
```
*(Note: Use `.\start.bat` in PowerShell rather than `start.bat`).*

---

### Option B: Running Services Separately

#### 1. Backend (FastAPI)
```powershell
# Optional: Seed database with initial stations, users, and vehicles
python -m backend.app.seed

# Optional: Retrain RL agents if needed
python -m backend.app.rl.train_agents

# Launch the FastAPI ASGI server
python -m uvicorn backend.app.main:app --reload --port 8000
```
* **API Server:** `http://localhost:8000`
* **Interactive Swagger UI:** `http://localhost:8000/docs`

#### 2. Frontend (React + Vite)
```powershell
cd frontend
npm install
npm run dev
```
* **Web Application:** `http://localhost:5173`

---

## 6. Pre-seeded Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@ev.local` | `admin123` |
| **Driver / User** | `user@ev.local` | `user123` |

---

## 7. Key REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `GET` | `/api/vehicles` | List user registered EVs |
| `POST` | `/api/battery/telemetry` | Record live battery voltage/current/temp |
| `GET` | `/api/battery/{id}/health` | Retrieve ML-predicted SoH & Remaining Useful Life |
| `GET` | `/api/stations` | Retrieve charging stations & coordinates |
| `POST` | `/api/bookings` | Reserve a charging bay |
| `POST` | `/api/rl/recommend` | Query RL policy for optimal charging decision |
| `GET` | `/api/analytics/dashboard` | Aggregated charging metrics & system trends |

---

## 8. Docker Deployment

To configure the backend and enable the Groq-powered EV Assistant, create a local environment file in the project root:
```powershell
Copy-Item .env.example .env
notepad .env
```
Replace `your_groq_api_key_here` with your Groq key and replace `generate_a_long_random_secret_here` with a unique, long random value for `JWT_SECRET_KEY`. The default model is `openai/gpt-oss-20b`; if you need to change it, set `GROQ_MODEL` to a model available to your Groq account. Docker Compose passes this file only to the backend. The `.env` file is ignored by Git; never commit or share it. The assistant is available in the dashboard after you sign in.

Run both services in containerized isolation:
```bash
docker compose up --build
```
* Backend container: Port `8000`
* Frontend container: Port `5173`
* API docs: `http://localhost:8000/docs`

The backend requires `JWT_SECRET_KEY` to start. If `GROQ_API_KEY` is not set, the rest of the app still runs; the assistant displays a configuration message until the key is added to `.env` and the backend container is recreated.
