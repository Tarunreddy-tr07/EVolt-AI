import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Vehicle Schemas ---
class VehicleCreate(BaseModel):
    vehicle_model: str = Field(..., max_length=100)
    battery_capacity: float = Field(..., gt=0)
    current_soc: float = Field(50.0, ge=0, le=100)
    current_soh: float = Field(100.0, ge=0, le=100)
    battery_temperature: float = Field(25.0, ge=-20, le=80)
    charging_type: str = Field("AC", max_length=20)

class VehicleOut(BaseModel):
    id: int
    user_id: int
    vehicle_model: str
    battery_capacity: float
    current_soc: float
    current_soh: float
    battery_temperature: float
    charging_type: str

    class Config:
        from_attributes = True


# --- Battery Telemetry Schemas ---
class BatteryTelemetryCreate(BaseModel):
    voltage: float
    current: float
    temperature: float
    soc: float
    soh: float

class BatteryTelemetryOut(BaseModel):
    id: int
    vehicle_id: int
    timestamp: datetime.datetime
    voltage: float
    current: float
    temperature: float
    soc: float
    soh: float

    class Config:
        from_attributes = True


# --- Charger & Station Schemas ---
class ChargerOut(BaseModel):
    id: int
    station_id: int
    charger_type: str
    power_kw: float
    status: str

    class Config:
        from_attributes = True

class ChargingStationOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    address: str
    total_chargers: int
    available_chargers: int
    electricity_price: float

    class Config:
        from_attributes = True


# --- Booking Schemas ---
class BookingCreate(BaseModel):
    station_id: int
    charger_id: int
    booking_time: datetime.datetime
    charging_mode: str = "Slow" # Fast, Slow

class BookingOut(BaseModel):
    id: int
    user_id: int
    vehicle_id: int
    station_id: int
    charger_id: int
    booking_time: datetime.datetime
    status: str

    class Config:
        from_attributes = True


# --- Charging Session Schemas ---
class ChargingSessionStart(BaseModel):
    vehicle_id: int
    station_id: int

class ChargingSessionOut(BaseModel):
    id: int
    vehicle_id: int
    station_id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    start_soc: float
    end_soc: Optional[float] = None
    energy_used: float
    cost: float

    class Config:
        from_attributes = True


# --- RL recommendation Schemas ---
class RLRecommendRequest(BaseModel):
    soc: float
    soh: float
    temperature: float
    electricity_price: float
    queue_length: int
    charger_availability: int
    distance: float
    charging_demand: float

class RLRecommendResponse(BaseModel):
    action: str
    station: str
    estimated_cost: float
    estimated_wait: int
    reward: float
    confidence: float
    reason: List[str]


# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    is_read: bool
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
