import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models.models import RLDecision, Vehicle, User
from backend.app.schemas.schemas import RLRecommendRequest, RLRecommendResponse
from backend.app.utils.auth_helper import get_current_user
from backend.app.services.rl_service import rl_service

router = APIRouter(prefix="/api/rl", tags=["Reinforcement Learning Engine"])

@router.post("/recommend", response_model=RLRecommendResponse)
def get_recommendation(
    req: RLRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find user's registered vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Register your vehicle first before requesting RL recommendations."
        )

    # Fetch recommendation from the trained RL service (defaults to DQN)
    res = rl_service.get_recommendation(
        soc=req.soc,
        soh=req.soh,
        temperature=req.temperature,
        price=req.electricity_price,
        queue_length=req.queue_length,
        charger_availability=req.charger_availability,
        distance=req.distance,
        charging_demand=req.charging_demand,
        agent_type="DQN"
    )

    # Log decision to SQLite for audit trace
    decision_log = RLDecision(
        vehicle_id=vehicle.id,
        state_json=json.dumps(req.model_dump()),
        selected_action=res["action"],
        reward=res["reward"],
        explanation=json.dumps(res["reason"])
    )
    db.add(decision_log)
    db.commit()

    return res


@router.post("/simulate", response_model=Dict[str, Any])
def run_charging_simulation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Simulate a step forward in the microgrid for Demo Mode
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(status_code=400, detail="Vehicle not found")

    # Simulate random state changes
    import random
    new_soc = min(100.0, vehicle.current_soc + random.uniform(5.0, 15.0))
    new_temp = min(60.0, vehicle.current_soc + random.uniform(1.0, 3.5))
    new_soh = max(70.0, vehicle.current_soh - random.uniform(0.01, 0.05))

    vehicle.current_soc = round(new_soc, 1)
    vehicle.battery_temperature = round(new_temp, 1)
    vehicle.current_soh = round(new_soh, 1)
    db.commit()

    return {
        "soc": vehicle.current_soc,
        "soh": vehicle.current_soh,
        "temperature": vehicle.battery_temperature,
        "message": "Simulated battery state updated successfully."
    }


@router.get("/history", response_model=List[Dict[str, Any]])
def get_rl_decisions_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    if not vehicle:
        return []

    logs = db.query(RLDecision).filter(RLDecision.vehicle_id == vehicle.id).order_by(RLDecision.timestamp.desc()).limit(10).all()
    
    out = []
    for l in logs:
        out.append({
            "id": l.id,
            "selected_action": l.selected_action,
            "reward": l.reward,
            "timestamp": l.timestamp,
            "state": json.loads(l.state_json),
            "explanation": json.loads(l.explanation)
        })
    return out
