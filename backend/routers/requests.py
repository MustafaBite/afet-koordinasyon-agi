from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

import models
import schemas
from database import SessionLocal
from priority_engine import calculate_dynamic_priority

router = APIRouter(prefix="/requests", tags=["requests"])


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
