import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models.models import Booking, User, Vehicle, ChargingStation, Charger, ChargingSession
from backend.app.schemas.schemas import BookingCreate, BookingOut
from backend.app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["Bookings & Queue"])

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify user has an EV registered
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must register a vehicle first before booking a charging slot."
        )

    # Verify station exists
    station = db.query(ChargingStation).filter(ChargingStation.id == booking_in.station_id).first()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charging station not found.")

    # Verify charger exists
    charger = db.query(Charger).filter(Charger.id == booking_in.charger_id).first()
    if not charger or charger.station_id != station.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charger not found at this station.")

    # Prevent booking duplicate slots
    existing_booking = db.query(Booking).filter(
        Booking.charger_id == charger.id,
        Booking.booking_time == booking_in.booking_time,
        Booking.status == "Confirmed"
    ).first()
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This slot is already booked for this charger. Please choose another time or charger."
        )

    new_booking = Booking(
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        station_id=station.id,
        charger_id=charger.id,
        booking_time=booking_in.booking_time,
        status="Confirmed"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


@router.get("", response_model=List[BookingOut])
def get_user_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    
    if booking.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    
    booking.status = "Cancelled"
    db.commit()
    return


@router.get("/queue/{station_id}", response_model=Dict[str, Any])
def get_queue_telemetry(station_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    station = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    # Queue calculations:
    # 1. Total Confirmed Bookings for this station today (or with booking time in the future)
    now = datetime.datetime.utcnow()
    today_start = datetime.datetime(now.year, now.month, now.day)
    
    bookings = db.query(Booking).filter(
        Booking.station_id == station_id,
        Booking.booking_time >= today_start,
        Booking.status == "Confirmed"
    ).order_by(Booking.booking_time.asc()).all()

    # Find where the current user is in this booking line
    user_pos = -1
    vehicles_ahead = 0
    estimated_wait = 0

    for i, b in enumerate(bookings):
        if b.user_id == current_user.id:
            user_pos = i + 1
            break
        vehicles_ahead += 1

    # Heuristic wait time: 10 minutes per vehicle ahead divided by total chargers
    if vehicles_ahead > 0:
        estimated_wait = max(5, int((vehicles_ahead * 25) / station.total_chargers))

    # Mock queue status lists to display on UI
    vehicle_cards = []
    for idx, b in enumerate(bookings[:4]):
        label = "YOU" if b.user_id == current_user.id else f"EV-{b.vehicle_id:02d}"
        vehicle_cards.append({
            "label": label,
            "position": idx + 1,
            "wait_min": max(0, idx * 8)
        })

    # If the user is not in the queue, add them at the end
    if user_pos == -1:
        user_pos = len(bookings) + 1
        vehicles_ahead = len(bookings)
        estimated_wait = max(5, int((vehicles_ahead * 25) / station.total_chargers))
        vehicle_cards.append({
            "label": "YOU (Estimated)",
            "position": user_pos,
            "wait_min": estimated_wait
        })

    return {
        "position": user_pos,
        "vehicles_ahead": vehicles_ahead,
        "estimated_wait": estimated_wait,
        "vehicle_cards": vehicle_cards
    }
