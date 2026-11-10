from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models.models import ChargingStation, Charger
from backend.app.schemas.schemas import ChargingStationOut, ChargerOut
from backend.app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/api/stations", tags=["Charging Stations"])

@router.get("", response_model=List[ChargingStationOut])
def get_stations(db: Session = Depends(get_db)):
    return db.query(ChargingStation).all()


@router.get("/{station_id}", response_model=Dict[str, Any])
def get_station_details(station_id: int, db: Session = Depends(get_db)):
    station = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Charging station not found"
        )
    
    chargers = db.query(Charger).filter(Charger.station_id == station_id).all()
    
    # Dynamically recount available chargers
    available_count = sum(1 for c in chargers if c.status == "Available")
    station.available_chargers = available_count
    db.commit()
    
    return {
        "id": station.id,
        "name": station.name,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "address": station.address,
        "total_chargers": station.total_chargers,
        "available_chargers": station.available_chargers,
        "electricity_price": station.electricity_price,
        "chargers": [
            {
                "id": c.id,
                "charger_type": c.charger_type,
                "power_kw": c.power_kw,
                "status": c.status
            }
            for c in chargers
        ]
    }
