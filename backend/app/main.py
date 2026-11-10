import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.database import engine, Base, get_db
from backend.app.models.models import User, Vehicle, ChargingSession, Booking, RLDecision
from backend.app.routers import auth, vehicles, stations, bookings, battery, rl_controller, chat

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EVolt Charging & Battery Management System (RL Engine)",
    description="FastAPI backend powered by Gymnasium Reinforcement Learning.",
    version="1.0.0"
)

# Enable CORS for frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(stations.router)
app.include_router(bookings.router)
app.include_router(battery.router)
app.include_router(rl_controller.router)
app.include_router(chat.router)


@app.get("/")
def read_root():
    return {"message": "EV Charging & Battery Management RL System API is online."}


@app.get("/api/analytics/dashboard", tags=["Analytics"])
def get_analytics_summary(db: Session = Depends(get_db)):
    # Calculate aggregated statistics
    total_sessions = db.query(ChargingSession).count()
    
    total_energy = db.query(ChargingSession).with_entities(
        ChargingSession.energy_used
    ).all()
    energy_sum = sum(x[0] for x in total_energy if x[0] is not None)
    
    total_cost = db.query(ChargingSession).with_entities(
        ChargingSession.cost
    ).all()
    cost_sum = sum(x[0] for x in total_cost if x[0] is not None)
    
    avg_charge_time = 45 # Mock default minutes
    avg_wait_time = 8 # Mock default minutes

    # Chart data mocks/summaries
    weekly_energy = [
        {"day": "Mon", "energy": 45},
        {"day": "Tue", "energy": 52},
        {"day": "Wed", "energy": 39},
        {"day": "Thu", "energy": 64},
        {"day": "Fri", "energy": 78},
        {"day": "Sat", "energy": 82},
        {"day": "Sun", "energy": 55}
    ]

    monthly_costs = [
        {"month": "Jan", "cost": 1200},
        {"month": "Feb", "cost": 1400},
        {"month": "Mar", "cost": 1100},
        {"month": "Apr", "cost": 1650},
        {"month": "May", "cost": 1800},
        {"month": "Jun", "cost": 2200},
        {"month": "Jul", "cost": 2100},
        {"month": "Aug", "cost": 1950}
    ]

    soh_trend = [
        {"cycle": 0, "soh": 100},
        {"cycle": 20, "soh": 99.1},
        {"cycle": 40, "soh": 98.2},
        {"cycle": 60, "soh": 97.4},
        {"cycle": 80, "soh": 96.5},
        {"cycle": 100, "soh": 95.7},
        {"cycle": 120, "soh": 94.8},
        {"cycle": 140, "soh": 94.0}
    ]

    utilization = [
        {"station": "Central Hub", "utilization": 74},
        {"station": "Anna Nagar", "utilization": 62},
        {"station": "T-Nagar", "utilization": 85},
        {"station": "Adyar Plaza", "utilization": 48}
    ]

    peak_hours = [
        {"hour": "00:00", "sessions": 2},
        {"hour": "04:00", "sessions": 1},
        {"hour": "08:00", "sessions": 8},
        {"hour": "12:00", "sessions": 14},
        {"hour": "16:00", "sessions": 19},
        {"hour": "20:00", "sessions": 25},
        {"hour": "22:00", "sessions": 10}
    ]

    return {
        "summary": {
            "total_sessions": total_sessions,
            "total_energy_kwh": round(energy_sum, 1),
            "total_cost_inr": round(cost_sum, 2),
            "avg_charging_time_min": avg_charge_time,
            "avg_waiting_time_min": avg_wait_time,
            "system_health": "Optimal"
        },
        "charts": {
            "weekly_energy": weekly_energy,
            "monthly_costs": monthly_costs,
            "soh_trend": soh_trend,
            "utilization": utilization,
            "peak_hours": peak_hours
        }
    }
