from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

import schemas
import models
from models import Cluster, ClusterStatus, ReliefVehicle
from core.dependencies import get_db
from services.clustering import run_clustering
from services.vehicle_recommendation import recommend_vehicles, NEED_TO_STOCK_FIELD

router = APIRouter(prefix="/requests/task-packages", tags=["clusters"])


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


@router.get("/{cluster_id}/recommend-vehicles", response_model=List[schemas.VehicleRecommendationResponse])
def recommend_vehicles_for_cluster(
    cluster_id: UUID,
    top_n: int = Query(3, ge=1, le=10, description="Kaç araç önerilecek"),
    db: Session = Depends(get_db)
):
    """
    Otonom Araç Önerisi Sistemi
    
    Bir küme için en uygun araçları AI ile önerir.
    - Mesafe (ETA)
    - Stok yeterliliği
    - Araç hızı
    - Aciliyet seviyesi
    
    Çok kriterli karar verme (MCDM) algoritması kullanır.
    """
    # Cluster'ı kontrol et
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster bulunamadı")
    
    # Araç önerilerini al
    recommendations = recommend_vehicles(db, str(cluster_id), top_n)
    
    if not recommendations:
        raise HTTPException(
            status_code=404, 
            detail="Uygun araç bulunamadı. Stok yetersiz veya araç mevcut değil."
        )
    
    # Response formatına dönüştür
    response = []
    for idx, rec in enumerate(recommendations):
        vehicle = rec["vehicle"]
        details = rec["details"]
        
        # Stok alanını belirle
        stock_field = NEED_TO_STOCK_FIELD.get(cluster.need_type.lower(), "tent_count")
        stock_name_map = {
            "tent_count": "çadır",
            "food_count": "gıda paketi",
            "water_count": "litre su",
            "medical_count": "medikal kit",
            "blanket_count": "battaniye"
        }
        stock_name = stock_name_map.get(stock_field, "malzeme")
        
        # AI tarafından oluşturulan açıklama metni
        if idx == 0:
            recommendation_text = (
                f"ÖNERİLEN ARAÇ: Bu kümenin {details['required_quantity']} {stock_name} ihtiyacı var. "
                f"En yakın ve stokta en az {details['required_quantity']} {stock_name} olan araç: "
                f"{vehicle.vehicle_type} ({vehicle.capacity}). "
                f"Mesafe: {details['distance_km']} km, "
                f"Tahmini Varış: {details['eta_minutes']} dakika. "
                f"Mevcut Stok: {details['available_stock']} {stock_name}. "
                f"⭐ Skor: {details['total_score']}/100"
            )
        else:
            recommendation_text = (
                f"Alternatif #{idx + 1}: {vehicle.vehicle_type} ({vehicle.capacity}). "
                f"Mesafe: {details['distance_km']} km, "
                f"ETA: {details['eta_minutes']} dk, "
                f"Stok: {details['available_stock']} {stock_name}. "
                f"Skor: {details['total_score']}/100"
            )
        
        response.append({
            "vehicle_id": vehicle.id,
            "vehicle_type": vehicle.vehicle_type,
            "capacity": vehicle.capacity,
            "latitude": vehicle.latitude,
            "longitude": vehicle.longitude,
            "base_speed_kmh": vehicle.base_speed_kmh or 60,
            "score": details["total_score"],
            "details": details,
            "recommendation_text": recommendation_text
        })
    
    return response


@router.post("/{cluster_id}/assign-vehicle")
def assign_vehicle_to_cluster(
    cluster_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Bir aracı kümeye atar ve stok günceller
    """
    # Cluster'ı kontrol et
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster bulunamadı")
    
    # Aracı kontrol et
    vehicle = db.query(ReliefVehicle).filter(ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")
    
    # Gerekli miktarı hesapla
    from services.vehicle_recommendation import calculate_required_quantity, NEED_TO_STOCK_FIELD
    required_quantity = calculate_required_quantity(
        cluster.need_type,
        cluster.total_persons_affected
    )
    
    # Stok kontrolü
    stock_field = NEED_TO_STOCK_FIELD.get(cluster.need_type.lower(), "tent_count")
    available_stock = getattr(vehicle, stock_field, 0)
    
    if available_stock < required_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Yetersiz stok. Gerekli: {required_quantity}, Mevcut: {available_stock}"
        )
    
    # Stoğu güncelle
    new_stock = available_stock - required_quantity
    setattr(vehicle, stock_field, new_stock)
    
    # Cluster durumunu güncelle
    cluster.status = ClusterStatus.resolved
    cluster.resolved_count = cluster.request_count
    cluster.pending_count = 0
    
    db.commit()
    db.refresh(vehicle)
    db.refresh(cluster)
    
    # ETA hesapla
    from services.vehicle_recommendation import calculate_haversine_distance, calculate_eta
    distance_km = calculate_haversine_distance(
        vehicle.latitude, vehicle.longitude,
        cluster.center_latitude, cluster.center_longitude
    )
    eta_minutes = calculate_eta(
        distance_km,
        vehicle.base_speed_kmh or 60,
        cluster.average_priority_score
    )
    
    return {
        "message": "Araç başarıyla atandı",
        "cluster_id": cluster_id,
        "vehicle_id": vehicle_id,
        "remaining_stock": new_stock,
        "distance_km": round(distance_km, 2),
        "eta_minutes": eta_minutes,
        "cluster_status": cluster.status
    }
