from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

import schemas
import models
from models import Cluster, ClusterStatus
from database import SessionLocal
from clustering_engine import run_clustering

router = APIRouter(prefix="/requests/task-packages", tags=["clusters"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _cluster_to_response(c: Cluster) -> dict:
    return {
        "cluster_id": c.id,
        "need_type": c.need_type,
        "cluster_name": c.cluster_name,
        "center_latitude": c.center_latitude,
        "center_longitude": c.center_longitude,
        "location": {
            "district": c.district,
            "neighborhood": c.neighborhood,
            "street": c.street,
            "full_address": c.full_address,
        },
        "request_count": c.request_count,
        "total_persons_affected": c.total_persons_affected,
        "average_priority_score": c.average_priority_score,
        "priority_level": c.priority_level,
        "status_summary": {
            "pending": c.pending_count,
            "assigned": c.assigned_count,
            "resolved": c.resolved_count,
        },
        "is_noise_cluster": bool(c.is_noise_cluster),
        "status": c.status,
        "generated_at": c.generated_at,
    }


@router.post("/generate", response_model=List[schemas.TaskPackageResponse], status_code=201)
def generate_task_packages(db: Session = Depends(get_db)):
    """Kümelemeyi çalıştırır, sonuçları DB'ye yazar ve döndürür."""
    clusters = run_clustering(db)
    return [_cluster_to_response(c) for c in clusters]


@router.get("", response_model=List[schemas.TaskPackageResponse])
def get_task_packages(
    need_type: Optional[str] = Query(None, description="Filter by need type (e.g. su, gida, medikal)"),
    status: Optional[str] = Query("active", description="Filter by status: active, resolved, all"),
    db: Session = Depends(get_db),
):
    """Mevcut kümeleri döndürür. status=all ile aktifler önce, resolved sonra gelir."""
    query = db.query(Cluster)

    if status == "all":
        clusters = query.order_by(
            Cluster.status.desc(),  # active > resolved alfabetik
            Cluster.average_priority_score.desc(),
        ).all()
        # active önce, resolved sonra — explicit sıralama
        active = [c for c in clusters if c.status == ClusterStatus.active]
        resolved = [c for c in clusters if c.status == ClusterStatus.resolved]
        clusters = active + resolved
    elif status == "resolved":
        query = query.filter(Cluster.status == ClusterStatus.resolved)
        clusters = query.order_by(Cluster.average_priority_score.desc()).all()
    else:
        query = query.filter(Cluster.status == ClusterStatus.active)
        clusters = query.order_by(Cluster.average_priority_score.desc()).all()

    if need_type:
        clusters = [c for c in clusters if c.need_type == need_type.lower()]

    return [_cluster_to_response(c) for c in clusters]


@router.get("/{cluster_id}", response_model=schemas.TaskPackageResponse)
def get_task_package(cluster_id: UUID, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return _cluster_to_response(cluster)
