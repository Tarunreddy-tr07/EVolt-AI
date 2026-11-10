import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER")  # USER, ADMIN
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    battery_capacity = Column(Float, nullable=False)  # in kWh
    current_soc = Column(Float, default=50.0)         # in %
    current_soh = Column(Float, default=100.0)        # in %
    battery_temperature = Column(Float, default=25.0) # in °C
    charging_type = Column(String(20), default="AC")  # AC, DC

    # Relationships
    owner = relationship("User", back_populates="vehicles")
    telemetry = relationship("BatteryTelemetry", back_populates="vehicle", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="vehicle", cascade="all, delete-orphan")
    sessions = relationship("ChargingSession", back_populates="vehicle", cascade="all, delete-orphan")
    decisions = relationship("RLDecision", back_populates="vehicle", cascade="all, delete-orphan")


class BatteryTelemetry(Base):
    __tablename__ = "battery_telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    voltage = Column(Float, nullable=False)     # in Volts
    current = Column(Float, nullable=False)     # in Amperes
    temperature = Column(Float, nullable=False) # in °C
    soc = Column(Float, nullable=False)         # in %
    soh = Column(Float, nullable=False)         # in %

    # Relationships
    vehicle = relationship("Vehicle", back_populates="telemetry")


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=False)
    total_chargers = Column(Integer, default=0)
    available_chargers = Column(Integer, default=0)
    electricity_price = Column(Float, default=8.5)  # in ₹/kWh

    # Relationships
    chargers = relationship("Charger", back_populates="station", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="station", cascade="all, delete-orphan")
    sessions = relationship("ChargingSession", back_populates="station", cascade="all, delete-orphan")


class Charger(Base):
    __tablename__ = "chargers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False)
    charger_type = Column(String(20), nullable=False) # Fast, Slow
    power_kw = Column(Float, nullable=False)          # e.g., 50.0, 7.4
    status = Column(String(20), default="Available")  # Available, Occupied, OutOfService

    # Relationships
    station = relationship("ChargingStation", back_populates="chargers")
    bookings = relationship("Booking", back_populates="charger")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False)
    charger_id = Column(Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False)
    booking_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="Confirmed")  # Confirmed, Completed, Cancelled

    # Relationships
    user = relationship("User", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")
    station = relationship("ChargingStation", back_populates="bookings")
    charger = relationship("Charger", back_populates="bookings")


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    start_soc = Column(Float, nullable=False)
    end_soc = Column(Float, nullable=True)
    energy_used = Column(Float, default=0.0)  # in kWh
    cost = Column(Float, default=0.0)         # in ₹

    # Relationships
    vehicle = relationship("Vehicle", back_populates="sessions")
    station = relationship("ChargingStation", back_populates="sessions")


class RLDecision(Base):
    __tablename__ = "rl_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    state_json = Column(Text, nullable=False)           # JSON input state
    selected_action = Column(String(50), nullable=False) # e.g. CHARGE_NOW, WAIT, FAST_CHARGE
    reward = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)           # JSON reason details
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="decisions")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # TEMP_WARNING, CHARGE_COMPLETE, etc.
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")
