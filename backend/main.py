from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from typing import List
import models
import schemas
from priority_engine import calculate_priority_score

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Veritabanı oturumu bağımlılığı
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}

@app.post("/talep-gonder", response_model=schemas.RequestResponse)
def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    db_request = models.AfetzedeTalep(**request_data.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/talepler/oncelikli", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized_requests(db: Session = Depends(get_db)):
    # Veritabanından tüm talepleri çek
    all_requests = db.query(models.AfetzedeTalep).all()

    results = []
    for req in all_requests:
        score = calculate_priority_score(req.need_type)
        results.append({
            "id": req.id,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "need_type": req.need_type,
            "created_at": req.created_at,
            "priority_score": score
        })

    # En yüksek puanlıdan en düşüğe sırala
    results.sort(key=lambda x: x["priority_score"], reverse=True)
    return results
