from live_earthquake_data import get_last_24h_earthquakes, get_major_earthquakes_last_3_months
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, SessionLocal
from typing import List, Optional
from pydantic import BaseModel
import models
import schemas
from priority_engine import calculate_dynamic_priority
import math
from math import sqrt
from datetime import datetime, timezone


# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afet Koordinasyon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'lar varsa ekle
try:
    from routers import requests as requests_router, clusters as clusters_router, auth as auth_router
    app.include_router(auth_router.router)
    app.include_router(requests_router.router)
    app.include_router(clusters_router.router)
except ImportError:
    pass

# Bağlı kullanıcıları yöneten class
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    # Yeni bağlantı ekleme
    async def connect(self, websocket: WebSocket):
        await websocket.accept()  # bağlantıyı kabul et
        self.active_connections.append(websocket)
        print("BAĞLANTI EKLENDİ:", len(self.active_connections))  # 


    # Bağlantı kopunca çıkar
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    # Tüm kullanıcılara mesaj gönder
    async def broadcast(self, message: dict):
        print("AKTİF BAĞLANTI SAYISI:", len(self.active_connections)) 
        for connection in self.active_connections:
            await connection.send_json(message)

# manager instance oluştur
manager = ConnectionManager()

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

# --- ENDPOINT'LER ---

@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Afet Koordinasyon API çalışıyor"}

# Eski endpoint (geriye dönük uyumluluk)
@app.post("/talep-gonder", response_model=schemas.RequestResponse)
def create_request_legacy(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    return _create_request(request_data, db)

# Yeni endpoint

@app.post("/requests")
async def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
   # return  _create_request(request_data, db)

    #def db_work():    
#def _create_request(request_data: schemas.RequestCreate, db: Session):
    earthquakes = get_last_24h_earthquakes()
    verified = is_near_earthquake(request_data.latitude, request_data.longitude, earthquakes)
    db_request = models.DisasterRequest(**request_data.model_dump(), is_verified=verified)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
       
    print("BURAYA GELDİ")
    print("AKTİF CONNECTION SAYISI:", len(manager.active_connections))#yeni
     # 🔥 EN KRİTİK
    for conn in manager.active_connections:
        await conn.send_json({
            "event": "NEW_REQUEST",
            "data": {
                "id": db_request.id,
                "need_type": db_request.need_type,
                "latitude": db_request.latitude,
                "longitude": db_request.longitude,
                "is_verified": verified
            }
        })
    
    return db_request

# Eski endpoint (geriye dönük uyumluluk)
@app.get("/talepler/oncelikli", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests_legacy(db: Session = Depends(get_db)):
    return _get_prioritized(db)

# Yeni endpoint
@app.get("/requests/prioritized", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests(db: Session = Depends(get_db)):
    return _get_prioritized(db)

def _get_prioritized(db: Session):
    all_requests = db.query(models.DisasterRequest).all()
    results = []
    for req in all_requests:
        score = calculate_dynamic_priority(req.need_type, req.created_at)
        results.append({
            "id": req.id,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "need_type": req.need_type,
            "person_count": getattr(req, "person_count", 1),
            "description": getattr(req, "description", None),
            "status": getattr(req, "status", "pending"),
            "created_at": req.created_at,
            "dynamic_priority_score": score,
            "is_verified": req.is_verified
        })
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    return results

@app.put("/requests/{request_id}/status")
def update_request_status(request_id: str, data: schemas.StatusUpdate, db: Session = Depends(get_db)):
    request = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    request.status = data.status
    db.commit()
    db.refresh(request)
    return request

@app.post("/arac-ekle")
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = models.ReliefVehicle(**vehicle.model_dump())
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
    return [v for v in vehicles if sqrt((v.latitude - lat)**2 + (v.longitude - lon)**2) < 0.1]

@app.get("/yakin-araclar-sql")
def get_nearby_sql(lat: float, lon: float, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM relief_vehicles"))
    return [dict(row._mapping) for row in result]

@app.get("/yakin-araclar-postgis")
def get_nearby_postgis(lat: float, lon: float, db: Session = Depends(get_db)):
    query = text("""
        SELECT * FROM relief_vehicles
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 5000)
    """)
    result = db.execute(query, {"lat": lat, "lon": lon})
    return [dict(row._mapping) for row in result]

@app.put("/arac-guncelle/{vehicle_id}")
def update_vehicle(vehicle_id: str, data: schemas.VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for field, value in data.model_dump().items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@app.get("/buyuk-depremler")
def get_major_earthquakes():
    """Son 3 ayda Türkiye'de gerçekleşen 5.0+ büyüklüğündeki depremler (yeniden eskiye)."""
    return get_major_earthquakes_last_3_months()

@app.post("/assign-vehicle")
def assign_vehicle(data: schemas.AssignVehicleRequest, db: Session = Depends(get_db)):
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    cluster = db.query(models.Cluster).filter(models.Cluster.id == data.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    needed = cluster.total_persons_affected
    if vehicle.tent_count < needed:
        raise HTTPException(status_code=400, detail="Not enough tent stock")
    vehicle.tent_count -= needed
    db.commit()
    db.refresh(vehicle)
    return {"message": "Vehicle assigned and stock updated", "remaining_tents": vehicle.tent_count}

# WebSocket bağlantılarını kabul eden ve yöneten ana endpoint
import asyncio
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)  #  sadece açık tutar
    except WebSocketDisconnect:
        manager.disconnect(websocket)