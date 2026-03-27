from fastapi import FastAPI, Depends, Query, HTTPException 
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from database import engine
import models
from routers import requests, clusters

import models
import schemas 
from database import engine, SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afet Koordinasyon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requests.router)
app.include_router(clusters.router)


@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}

@app.post("/requests", response_model=schemas.RequestResponse)
def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    db_request = models.DisasterRequest(**request_data.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/requests/prioritized", response_model=List[schemas.PrioritizedRequestResponse])
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
            "dynamic_priority_score": score
        })

    # 1. En yüksek dinamik puandan en düşüğe sırala.
    # 2. Eğer puanlar eşitse (Örn: ikisi de 1000 olduysa), en eski tarihli olanı (ilk bekleyeni) öne al.
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    
    return results
from pydantic import BaseModel

class VehicleCreate(BaseModel):
    latitude: float
    longitude: float
    vehicle_type: str
    capacity: str


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
    vehicles = db.query(models.ReliefVehicle).all()
    return vehicles

from math import sqrt

@app.get("/yakin-araclar")
def get_nearby_vehicles(lat: float, lon: float, db: Session = Depends(get_db)):
    vehicles = db.query(models.ReliefVehicle).all()

    nearby = []

    for v in vehicles:
        distance = sqrt((v.latitude - lat)**2 + (v.longitude - lon)**2)

        if distance < 0.1:  # yaklaşık 5-10 km gibi
            nearby.append(v)

    return nearby

from sqlalchemy import text

@app.get("/yakin-araclar-sql")
def get_nearby_sql(lat: float, lon: float, db: Session = Depends(get_db)):

    query = text("""
        SELECT * FROM relief_vehicles
    """)

    result = db.execute(query)

    vehicles = []

    for row in result:
      vehicles.append(dict(row._mapping))

    return vehicles
from sqlalchemy import text

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

    vehicles = []
    for row in result:
        vehicles.append(dict(row._mapping))

    return vehicles

from pydantic import BaseModel

class VehicleUpdate(BaseModel):
    tent_count: int
    food_count: int
    water_count: int
    medical_count: int
    blanket_count: int


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


@app.get("/requests/task-packages", response_model=List[schemas.TaskPackageResponse])
def get_task_packages(
    need_type: Optional[str] = Query(None, description="İhtiyaç tipine göre filtrele (ör: su, gida, medikal)"),
    db: Session = Depends(get_db),
):
    """
    Görev 3.6 & 3.7 — Mekansal Kümeleme ve Görev Paketi Üretimi.

    Aynı tip ve 500m yakınlıktaki talepleri DBSCAN ile kümeleyip,
    ters geocoding ile adres bilgisi eklenmiş görev paketleri döner.
    """
    packages = generate_task_packages(db, need_type_filter=need_type)
    return packages
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Afet Koordinasyon API çalışıyor"}

@app.put("/requests/{request_id}/status")
def update_request_status(
    request_id: str,
    data: schemas.StatusUpdate,
    db: Session = Depends(get_db)
):
    request = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = data.status

    db.commit()
    db.refresh(request)

    return request
#
from schemas import AssignVehicleRequest

@app.post("/assign-vehicle")
def assign_vehicle(data: AssignVehicleRequest, db: Session = Depends(get_db)):

    # 1️⃣ Araç bul
    vehicle = db.query(models.ReliefVehicle).filter(
        models.ReliefVehicle.id == data.vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 2️⃣ Cluster bul
    cluster = db.query(models.Cluster).filter(
        models.Cluster.id == data.cluster_id
    ).first()

    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # 3️⃣ Kaç kişi? (ihtiyaç miktarı)
    needed = cluster.total_persons_affected

    # 4️⃣ Stok kontrolü
    if vehicle.tent_count < needed:
        raise HTTPException(status_code=400, detail="Not enough tent stock")

    # 5️⃣ STOK DÜŞÜR 💥
    vehicle.tent_count -= needed

    # 6️⃣ Commit
    db.commit()
    db.refresh(vehicle)

    return {
        "message": "Vehicle assigned and stock updated",
        "remaining_tents": vehicle.tent_count
    }
