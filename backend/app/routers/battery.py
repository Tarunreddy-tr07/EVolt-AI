import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models.models import BatteryTelemetry, Vehicle, User
from backend.app.schemas.schemas import BatteryTelemetryOut, BatteryTelemetryCreate
from backend.app.utils.auth_helper import get_current_user
from backend.app.services.ml_service import ml_service

router = APIRouter(prefix="/api/battery", tags=["Battery Intelligence"])

@router.get("/{vehicle_id}", response_model=List[BatteryTelemetryOut])
def get_telemetry_history(vehicle_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if vehicle.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return db.query(BatteryTelemetry).filter(
        BatteryTelemetry.vehicle_id == vehicle_id
    ).order_by(BatteryTelemetry.timestamp.asc()).all()


@router.post("/telemetry", response_model=BatteryTelemetryOut, status_code=status.HTTP_201_CREATED)
def create_telemetry_reading(telemetry_in: BatteryTelemetryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Find active vehicle of user
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Register your vehicle first to record telemetry."
        )

    # Calculate SOC using our ML Random Forest model
    # Heuristics for elapsed fraction if not directly supplied (assume 50% through session)
    inferred_soc = ml_service.predict_soc(
        time_elapsed_frac=0.5,
        charge_rate_kw=telemetry_in.current * telemetry_in.voltage / 1000.0,
        battery_capacity_kwh=vehicle.battery_capacity,
        energy_delivered_kwh=vehicle.battery_capacity * (telemetry_in.soc / 100.0)
    )

    db_telemetry = BatteryTelemetry(
        vehicle_id=vehicle.id,
        voltage=telemetry_in.voltage,
        current=telemetry_in.current,
        temperature=telemetry_in.temperature,
        soc=telemetry_in.soc,
        soh=telemetry_in.soh
    )
    
    # Update vehicle's current state variables
    vehicle.current_soc = telemetry_in.soc
    vehicle.current_soh = telemetry_in.soh
    vehicle.battery_temperature = telemetry_in.temperature
    
    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)
    return db_telemetry


@router.get("/{vehicle_id}/health", response_model=Dict[str, Any])
def get_battery_health(vehicle_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if vehicle.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Cycle count heuristic (if not stored, assume 150 cycles)
    cycle_count = 150
    predicted_soh = ml_service.predict_soh(
        cycle_count=cycle_count,
        avg_discharge_rate_c=0.5,
        depth_of_discharge=0.8,
        avg_temperature_c=vehicle.battery_temperature
    )

    soh_pct = predicted_soh * 100
    health_status = ml_service.get_health_label(predicted_soh)

    # Estimate remaining useful life (RUL)
    # A battery is end-of-life when SOH hits 70% or 80%. Let's assume 75%
    fade_per_cycle = (1.0 - predicted_soh) / max(1, cycle_count)
    remaining_cycles = int((predicted_soh - 0.75) / max(fade_per_cycle, 0.0001))
    remaining_cycles = max(0, min(1500, remaining_cycles))
    remaining_years = round(remaining_cycles / 200.0, 1) # Assumes 200 full cycles/year

    return {
        "vehicle_id": vehicle.id,
        "soh": round(soh_pct, 1),
        "health_status": health_status,
        "cycle_count": cycle_count,
        "predicted_cycles_remaining": remaining_cycles,
        "estimated_years_remaining": remaining_years,
        "temperature_warning": vehicle.battery_temperature > 40.0
    }


@router.post("/{vehicle_id}/predict", response_model=Dict[str, Any])
def get_degradation_predictions(vehicle_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if vehicle.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Generate degradation curve data for 100 future charge cycles
    cycle_count = 150
    historical_cycles = list(range(0, cycle_count + 1, 10))
    predicted_cycles = list(range(cycle_count, cycle_count + 501, 50))

    history_points = []
    for c in historical_cycles:
        soh = ml_service.predict_soh(c, avg_temperature_c=25.0)
        history_points.append({"cycle": c, "soh": round(soh * 100, 1), "type": "Historical"})

    predicted_points = []
    for c in predicted_cycles:
        soh_normal = ml_service.predict_soh(c, avg_temperature_c=25.0)
        soh_abuse = ml_service.predict_soh(c, avg_temperature_c=42.0) # High temp fade
        predicted_points.append({
            "cycle": c, 
            "soh_normal": round(soh_normal * 100, 1),
            "soh_abuse": round(soh_abuse * 100, 1),
            "type": "Predicted"
        })

    return {
        "current_soh": round(vehicle.current_soh, 1),
        "cycle_count": cycle_count,
        "historical_curve": history_points,
        "predicted_curve": predicted_points
    }
