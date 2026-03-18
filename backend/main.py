from live_earthquake_data import get_last_24h_earthquakes
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, SessionLocal
from typing import List
from pydantic import BaseModel
import models
import schemas
from priority_engine import calculate_dynamic_priority
import math
from math import sqrt
from datetime import datetime, timezone

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- YARDIMCI FONKSİYONLAR ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine Formülü ile iki nokta arası mesafe hesaplama (km)"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_near_earthquake(lat, lon, earthquakes):
    """İhbarın deprem bölgesine yakınlığını kontrol eder (50km)"""
    if not earthquakes:
        return False

    for eq in earthquakes:
        eq_lat = eq.get("lat") or eq.get("latitude")
        eq_lon = eq.get("lon") or eq.get("longitude")

        if eq_lat and eq_lon:
            distance = calculate_distance(lat, lon, float(eq_lat), float(eq_lon))
            if distance <= 50:
                return True
    return False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC MODELLER ---

class VehicleCreate(BaseModel):
    latitude: float
    longitude: float
    vehicle_type: str
    capacity: str

class VehicleUpdate(BaseModel):
    tent_count: int
    food_count: int
    water_count: int
    medical_count: int
    blanket_count: int

# --- ENDPOINT'LER ---

@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}

@app.post("/talep-gonder", response_model=schemas.RequestResponse)
def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    # 1. Güncel deprem verilerini çek
    earthquakes = get_last_24h_earthquakes()

    # 2. Cross-Check (Doğrulama)
    verified = is_near_earthquake(
        request_data.latitude,
        request_data.longitude,
        earthquakes
    )

    # 3. Veritabanına kaydet
    db_request = models.DisasterRequest(
        **request_data.model_dump(),
        is_verified=verified
    )

    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    return db_request

@app.get("/talepler/oncelikli", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests(db: Session = Depends(get_db)):
    all_requests = db.query(models.DisasterRequest).all()

    results = []
    for req in all_requests:
        score = calculate_dynamic_priority(req.need_type, req.created_at)
        results.append({
            "id": req.id,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "need_type": req.need_type,
            "created_at": req.created_at,
            "dynamic_priority_score": score,
            "is_verified": req.is_verified
        })

    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))

    return results

@app.post("/arac-ekle")
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = models.ReliefVehicle(
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        vehicle_type=vehicle.vehicle_type,
        capacity=vehicle.capacity
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

@app.get("/araclar")
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(models.ReliefVehicle).all()

@app.get("/yakin-araclar")
def get_nearby_vehicles(lat: float, lon: float, db: Session = Depends(get_db)):
    vehicles = db.query(models.ReliefVehicle).all()
    nearby = []
    for v in vehicles:
        distance = sqrt((v.latitude - lat)**2 + (v.longitude - lon)**2)
        if distance < 0.1:
            nearby.append(v)
    return nearby

@app.get("/yakin-araclar-sql")
def get_nearby_sql(lat: float, lon: float, db: Session = Depends(get_db)):
    query = text("SELECT * FROM relief_vehicles")
    result = db.execute(query)
    return [dict(row._mapping) for row in result]

@app.get("/yakin-araclar-postgis")
def get_nearby_postgis(lat: float, lon: float, db: Session = Depends(get_db)):
    query = text("""
        SELECT *
        FROM relief_vehicles
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            5000
        )
    """)
    result = db.execute(query, {"lat": lat, "lon": lon})
    return [dict(row._mapping) for row in result]

@app.put("/arac-guncelle/{vehicle_id}")
def update_vehicle(vehicle_id: str, data: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.tent_count = data.tent_count
    vehicle.food_count = data.food_count
    vehicle.water_count = data.water_count
    vehicle.medical_count = data.medical_count
    vehicle.blanket_count = data.blanket_count
    db.commit()
    db.refresh(vehicle)
    return vehicle
