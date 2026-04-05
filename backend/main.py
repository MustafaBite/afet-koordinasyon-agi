from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from math import sqrt
import asyncio

from database import engine
from core.dependencies import get_db
from utils.geo import calculate_distance, is_near_earthquake
from utils.websocket import ConnectionManager
from live_earthquake_data import get_last_24h_earthquakes, get_major_earthquakes_last_3_months
from services.priority import calculate_dynamic_priority
import models
import schemas


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

# Router'ları ekle
try:
    from routers import requests as requests_router, clusters as clusters_router, auth as auth_router, vehicles as vehicles_router
    app.include_router(auth_router.router)
    app.include_router(requests_router.router, prefix="/api/ihbarlar")
    app.include_router(clusters_router.router)
    app.include_router(vehicles_router.router)
except Exception as e: 
    print(f"ROUTER HATASI: {e}")

# WebSocket manager instance
manager = ConnectionManager()

# --- ENDPOINT'LER ---

@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Afet Koordinasyon API çalışıyor"}


# --- İHBAR YÖNETİMİ ---

@app.post("/talep-gonder", response_model=schemas.RequestResponse)
def create_request_legacy(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    """Eski endpoint (geriye dönük uyumluluk)"""
    return _create_request_sync(request_data, db)


@app.post("/requests")
async def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    """Yeni ihbar oluştur ve WebSocket ile bildir"""
    earthquakes = get_last_24h_earthquakes()
    verified = is_near_earthquake(request_data.latitude, request_data.longitude, earthquakes)
    
    db_request = models.DisasterRequest(**request_data.model_dump(), is_verified=verified)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # WebSocket ile tüm bağlı kullanıcılara bildir
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


def _create_request_sync(request_data: schemas.RequestCreate, db: Session):
    """Senkron ihbar oluşturma (legacy endpoint için)"""
    earthquakes = get_last_24h_earthquakes()
    verified = is_near_earthquake(request_data.latitude, request_data.longitude, earthquakes)
    
    db_request = models.DisasterRequest(**request_data.model_dump(), is_verified=verified)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request

@app.get("/talepler/oncelikli", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests_legacy(db: Session = Depends(get_db)):
    """Eski endpoint (geriye dönük uyumluluk)"""
    return _get_prioritized(db)


@app.get("/requests/prioritized", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests(db: Session = Depends(get_db)):
    """Önceliklendirilmiş ihbarları getir"""
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
    """İhbar durumunu güncelle"""
    request = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    request.status = data.status
    db.commit()
    db.refresh(request)
    return request


# --- ARAÇ YÖNETİMİ (Legacy Endpoints) ---

@app.post("/arac-ekle")
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    """Eski endpoint - Yeni araç ekle"""
    new_vehicle = models.ReliefVehicle(**vehicle.model_dump())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


@app.get("/araclar")
def get_vehicles(db: Session = Depends(get_db)):
    """Eski endpoint - Tüm araçları listele"""
    return db.query(models.ReliefVehicle).all()


@app.get("/yakin-araclar")
def get_nearby_vehicles(lat: float, lon: float, db: Session = Depends(get_db)):
    """Eski endpoint - Yakındaki araçları getir"""
    vehicles = db.query(models.ReliefVehicle).all()
    return [v for v in vehicles if sqrt((v.latitude - lat)**2 + (v.longitude - lon)**2) < 0.1]


@app.get("/yakin-araclar-sql")
def get_nearby_sql(lat: float, lon: float, db: Session = Depends(get_db)):
    """Eski endpoint - SQL ile yakındaki araçlar"""
    result = db.execute(text("SELECT * FROM relief_vehicles"))
    return [dict(row._mapping) for row in result]


@app.get("/yakin-araclar-postgis")
def get_nearby_postgis(lat: float, lon: float, db: Session = Depends(get_db)):
    """Eski endpoint - PostGIS ile yakındaki araçlar"""
    query = text("""
        SELECT * FROM relief_vehicles
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 5000)
    """)
    result = db.execute(query, {"lat": lat, "lon": lon})
    return [dict(row._mapping) for row in result]


@app.put("/arac-guncelle/{vehicle_id}")
def update_vehicle(vehicle_id: str, data: schemas.VehicleUpdate, db: Session = Depends(get_db)):
    """Eski endpoint - Araç bilgilerini güncelle"""
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for field, value in data.model_dump().items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.post("/assign-vehicle")
def assign_vehicle(data: schemas.AssignVehicleRequest, db: Session = Depends(get_db)):
    """Eski endpoint - Aracı kümeye ata"""
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


# --- DEPREM VERİLERİ ---

@app.get("/buyuk-depremler")
def get_major_earthquakes():
    """Son 3 ayda Türkiye'de gerçekleşen 5.0+ büyüklüğündeki depremler"""
    return get_major_earthquakes_last_3_months()


# --- WEBSOCKET ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket bağlantılarını yönet"""
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- OPERASYON YÖNETİMİ ---

class SuruBaslatSchema(BaseModel):
    sektor_id: str
    aksiyon: str


@app.post("/api/operasyon/suru-baslat")
async def start_swarm_operation(data: SuruBaslatSchema):
    """Otonom sürü operasyonu başlat"""
    print(f"OPERASYON: {data.sektor_id} bölgesinde {data.aksiyon} tetiklendi!")
    
    await manager.broadcast({
        "event": "SWARM_STARTED",
        "sector": data.sektor_id,
        "action": data.aksiyon
    })
    return {"status": "started", "detail": f"{data.sektor_id} için operasyon başladı."}