from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

import models
import schemas
from database import SessionLocal
from services.priority import calculate_dynamic_priority

#router = APIRouter(prefix="/requests", tags=["requests"]) // bu silinicek 
router = APIRouter(tags=["requests"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.RequestResponse, status_code=201)
def create_request(body: schemas.RequestCreate, db: Session = Depends(get_db)):
    req = models.DisasterRequest(**body.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/prioritized", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized(db: Session = Depends(get_db)):
    all_requests = db.query(models.DisasterRequest).all()
    results = []
    for req in all_requests:
        score = calculate_dynamic_priority(req.need_type, req.created_at)
        results.append({
            "id": req.id,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "need_type": req.need_type,
            "person_count": req.person_count,
            "description": req.description,
            "status": req.status,
            "created_at": req.created_at,
            "is_verified": req.is_verified,
            "dynamic_priority_score": score,
        })
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    return results


@router.patch("/{request_id}/status", response_model=schemas.RequestResponse)
def update_status(request_id: UUID, body: schemas.StatusUpdate, db: Session = Depends(get_db)):
    req = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = body.status
    db.commit()
    db.refresh(req)
    return req
# 1. DOĞRULANMAMIŞ İHBARLARI LİSTELE (Filtreli)
@router.get("/dogrulanmamis")
def get_dogrulanmamis_ihbarlar(
    oncelik: str = Query(None), # Zehra'nın ?oncelik=yuksek filtresi
    db: Session = Depends(get_db)
):
    # Veritabanında is_verified=False olanları bul
    query = db.query(models.DisasterRequest).filter(models.DisasterRequest.is_verified == False)
    
    if oncelik:
        # Zehra 'yuksek' veya 'dusuk' gönderirse need_type üzerinden süzüyoruz
        query = query.filter(models.DisasterRequest.need_type == oncelik)
    
    return query.all()

# 2. DOĞRULA BUTONU (POST)
@router.post("/{request_id}/dogrula")
def verify_request(request_id: UUID, db: Session = Depends(get_db)):
    req = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı")
    
    req.is_verified = True # Artık doğrulandı!
    db.commit()
    return {"status": "success", "message": "İhbar doğrulandı."}

# 3. REDDET BUTONU (POST)
@router.post("/{request_id}/reddet")
def reject_request(request_id: UUID, db: Session = Depends(get_db)):
    req = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı")
    
    db.delete(req) # Reddedilen ihbarı siliyoruz
    db.commit()
    return {"status": "success", "message": "İhbar silindi."}

# Toplam, doğrulanan ve bekleyen ihbar sayılarını hesaplayarak arayüze gönderir.
@router.get("/istatistikler")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(models.DisasterRequest).count()
    verified = db.query(models.DisasterRequest).filter(models.DisasterRequest.is_verified == True).count()
    pending = total - verified
    
    return {
        "toplam_ihbar": total,
        "dogrulanan_ihbar": verified,
        "bekleyen_ihbar": pending,
        "basari_orani": f"{(verified/total)*100:.2f}%" if total > 0 else "0%"
    }