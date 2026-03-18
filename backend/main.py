from live_earthquake_data import get_last_24h_earthquakes
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from typing import List
import models
import schemas
from priority_engine import calculate_dynamic_priority
import math
from datetime import datetime, timezone

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- YARDIMCI FONKSİYONLAR (Endpoint'lerden önce tanımlanmalı) ---

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
        # API'den gelen farklı anahtar isimlerine karşı esneklik
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

@app.post("/talep-gonder", response_model=schemas.RequestResponse)
def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    # 1. Güncel deprem verilerini çek
    earthquakes = get_last_24h_earthquakes()

    # 2. Güvenlik Duvarı: Cross-Check (Doğrulama)
    verified = is_near_earthquake(
        request_data.latitude,
        request_data.longitude,
        earthquakes
    )

    # 3. Veritabanına kaydet (model_dump() yeni standarttır, hata alırsan .dict() yapabilirsin)
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
            "is_verified": req.is_verified # Bunu da listeye eklemek iyi olabilir
        })

    # Önceliklendirme sıralaması
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    
    return results