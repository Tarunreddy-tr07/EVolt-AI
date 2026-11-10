from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models.models import Vehicle, User
from backend.app.schemas.schemas import VehicleCreate, VehicleOut
from backend.app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle_in: VehicleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_vehicle = Vehicle(
        user_id=current_user.id,
        vehicle_model=vehicle_in.vehicle_model,
        battery_capacity=vehicle_in.battery_capacity,
        current_soc=vehicle_in.current_soc,
        current_soh=vehicle_in.current_soh,
        battery_temperature=vehicle_in.battery_temperature,
        charging_type=vehicle_in.charging_type
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.get("", response_model=List[VehicleOut])
def get_vehicles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle_by_id(vehicle_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if vehicle.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, vehicle_in: VehicleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if db_vehicle.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    db_vehicle.vehicle_model = vehicle_in.vehicle_model
    db_vehicle.battery_capacity = vehicle_in.battery_capacity
    db_vehicle.current_soc = vehicle_in.current_soc
    db_vehicle.current_soh = vehicle_in.current_soh
    db_vehicle.battery_temperature = vehicle_in.battery_temperature
    db_vehicle.charging_type = vehicle_in.charging_type
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle
