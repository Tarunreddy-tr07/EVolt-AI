import datetime
import bcrypt
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.models import User, Vehicle, ChargingStation, Charger, BatteryTelemetry, ChargingSession, Booking

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def seed_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if database is already seeded
    if db.query(User).filter(User.email == "user@ev.local").first():
        print("Database already seeded.")
        db.close()
        return

    print("Seeding database...")

    # Users
    admin = User(name="Ganesh Admin", email="admin@ev.local", password_hash=hash_password("admin123"), role="ADMIN")
    user = User(name="Ganesh User", email="user@ev.local", password_hash=hash_password("user123"), role="USER")
    db.add(admin)
    db.add(user)
    db.commit()

    # Vehicle
    vehicle = Vehicle(
        user_id=user.id,
        vehicle_model="Tesla Model 3 Long Range",
        battery_capacity=75.0,
        current_soc=28.0,
        current_soh=94.0,
        battery_temperature=31.0,
        charging_type="DC"
    )
    db.add(vehicle)
    db.commit()

    # Charging Stations
    station_data = [
        {"name": "GreenCharge Central Hub", "latitude": 13.0827, "longitude": 80.2707, "address": "Chennai Central Railway Station, Chennai", "price": 8.5},
        {"name": "Anna Nagar Smart Hub", "latitude": 13.0850, "longitude": 80.2101, "address": "Anna Nagar Tower Park Complex, Chennai", "price": 9.5},
        {"name": "T-Nagar EV Station", "latitude": 13.0406, "longitude": 80.2337, "address": "Pondy Bazaar Pedestrian Plaza, Chennai", "price": 10.0},
        {"name": "Adyar EcoCharge Plaza", "latitude": 13.0063, "longitude": 80.2574, "address": "Adyar Flyover Junction, Chennai", "price": 7.5}
    ]

    stations = []
    for s_info in station_data:
        station = ChargingStation(
            name=s_info["name"],
            latitude=s_info["latitude"],
            longitude=s_info["longitude"],
            address=s_info["address"],
            electricity_price=s_info["price"],
            total_chargers=6,
            available_chargers=4
        )
        db.add(station)
        db.flush()
        stations.append(station)

        # Chargers for each station
        # 3 Fast Chargers (DC 50kW), 3 Slow Chargers (AC 7.4kW)
        for i in range(3):
            fc = Charger(
                station_id=station.id, 
                charger_type="Fast", 
                power_kw=50.0, 
                status="Available" if i != 0 else "Occupied"
            )
            sc = Charger(
                station_id=station.id, 
                charger_type="Slow", 
                power_kw=7.4, 
                status="Available"
            )
            db.add(fc)
            db.add(sc)

    db.commit()

    # Add historical battery telemetry for graphs
    now = datetime.datetime.utcnow()
    for i in range(20):
        t_stamp = now - datetime.timedelta(hours=(20 - i))
        # SOC slowly decaying or rising
        soc_val = 80.0 - (i * 2.5) if i < 12 else 10.0 + ((i - 12) * 8.0)
        telemetry = BatteryTelemetry(
            vehicle_id=vehicle.id,
            timestamp=t_stamp,
            voltage=380.0 + (soc_val * 0.4),
            current=-20.0 if i < 12 else 80.0, # Negative means discharging, Positive means charging
            temperature=28.0 + (i * 0.15) if i < 12 else 31.0 + ((i - 12) * 0.4),
            soc=soc_val,
            soh=94.5 - (i * 0.01)
        )
        db.add(telemetry)

    # Seed some historical sessions
    for i in range(5):
        s_date = now - datetime.timedelta(days=(5 - i))
        st = stations[i % len(stations)]
        session = ChargingSession(
            vehicle_id=vehicle.id,
            station_id=st.id,
            start_time=s_date,
            end_time=s_date + datetime.timedelta(minutes=45),
            start_soc=15.0 + i * 5,
            end_soc=80.0,
            energy_used=30.0 + i * 2,
            cost=(30.0 + i * 2) * st.electricity_price
        )
        db.add(session)

    # Seed a future booking
    booking = Booking(
        user_id=user.id,
        vehicle_id=vehicle.id,
        station_id=stations[0].id,
        charger_id=1,  # First charger
        booking_time=now + datetime.timedelta(days=1),
        status="Confirmed"
    )
    db.add(booking)

    db.commit()
    db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_db()
