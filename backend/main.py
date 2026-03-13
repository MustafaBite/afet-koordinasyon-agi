from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from typing import List
import models
import schemas
from priority_engine import calculate_dynamic_priority

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    db_request = models.DisasterRequest(**request_data.dict())
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
            "dynamic_priority_score": score
        })

    results.sort(key=lambda x: x["dynamic_priority_score"], reverse=True)
    return results
