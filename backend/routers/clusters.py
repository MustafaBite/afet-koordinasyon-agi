from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

import schemas
from models import Cluster, ClusterStatus, ReliefVehicle
from constants import VehicleStatus
from core.dependencies import get_db, require_coordinator
from services.clustering import run_clustering
from services.vehicle_recommendation import recommend_vehicles, NEED_TO_STOCK_FIELD
from services.override_detector import detect_override_opportunities
from services.priority import calculate_priority_with_context

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
def generate_task_packages(db: Session = Depends(get_db), _=Depends(require_coordinator)):
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
            Cluster.status.desc(),
            Cluster.average_priority_score.desc(),
        ).all()
        active = [c for c in clusters if c.status == ClusterStatus.active]
        en_route = [c for c in clusters if c.status == ClusterStatus.en_route]
        resolved = [c for c in clusters if c.status == ClusterStatus.resolved]
        clusters = active + en_route + resolved
    elif status == "resolved":
        query = query.filter(Cluster.status == ClusterStatus.resolved)
        clusters = query.order_by(Cluster.average_priority_score.desc()).all()
    elif status == "en_route":
        query = query.filter(Cluster.status == ClusterStatus.en_route)
        clusters = query.order_by(Cluster.average_priority_score.desc()).all()
    else:
        # "active" varsayılanı: hem aktif hem de en_route kümeler döner
        # (Dashboard yolda kümeleri sarı kart olarak göstersin diye)
        query = query.filter(
            Cluster.status.in_([ClusterStatus.active, ClusterStatus.en_route])
        )
        clusters = query.order_by(
            Cluster.status.asc(),
            Cluster.average_priority_score.desc(),
        ).all()

    if need_type:
        clusters = [c for c in clusters if c.need_type == need_type.lower()]

    return [_cluster_to_response(c) for c in clusters]


# ──────────────────────────────────────────────────────────────────────────
# Statik-path endpoint'ler — /{cluster_id} dinamik route'undan ÖNCE tanımlanmalı
# (Aksi halde FastAPI 'override-alerts' string'ini UUID parse etmeye çalışır)
# ──────────────────────────────────────────────────────────────────────────

@router.get("/override-alerts", response_model=List[schemas.OverrideAlertResponse])
def get_override_alerts(db: Session = Depends(get_db)):
    """
    Yolda olan araçlar için 'Aracı Kaydır' önerilerini döndürür.

    AI Politikası:
    - Yeni küme tipi medikal/arama_kurtarma ise daima öneri üretir
    - Yeni kümenin puanı, mevcut hedeften +20 puan üstündeyse öneri üretir
    - Aracın 50 km'den uzakta olduğu kümeler eler
    """
    return detect_override_opportunities(db)


@router.post("/execute-override")
def execute_override(
    payload: schemas.ExecuteOverrideRequest,
    db: Session = Depends(get_db),
    _=Depends(require_coordinator),
):
    """
    Yetkilinin onayı ile bir aracı yeni kümeye yönlendirir.
    Eski küme tekrar 'active' statüsüne döner, yeni küme 'yolda' olur.
    Stok hareketi otomatik yeniden hesaplanır.
    """
    vehicle = (
        db.query(ReliefVehicle)
        .filter(ReliefVehicle.id == payload.vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")

    if vehicle.vehicle_status != VehicleStatus.EN_ROUTE or not vehicle.assigned_cluster_id:
        raise HTTPException(status_code=400, detail="Araç şu an yolda değil")

    new_cluster = (
        db.query(Cluster).filter(Cluster.id == payload.new_cluster_id).first()
    )
    if not new_cluster:
        raise HTTPException(status_code=404, detail="Hedef küme bulunamadı")

    if new_cluster.status != ClusterStatus.active:
        raise HTTPException(
            status_code=400,
            detail=f"Hedef küme aktif değil (mevcut: {new_cluster.status})"
        )

    old_cluster = (
        db.query(Cluster)
        .filter(Cluster.id == vehicle.assigned_cluster_id)
        .first()
    )

    from services.vehicle_recommendation import calculate_required_quantity

    if old_cluster:
        old_stock_field = NEED_TO_STOCK_FIELD.get(
            old_cluster.need_type.lower(), "tent_count"
        )
        old_required = calculate_required_quantity(
            old_cluster.need_type, old_cluster.total_persons_affected
        )
        current_old_stock = getattr(vehicle, old_stock_field, 0)
        setattr(vehicle, old_stock_field, current_old_stock + old_required)

        old_cluster.status = ClusterStatus.active
        old_cluster.pending_count = old_cluster.request_count
        old_cluster.assigned_count = 0

    new_stock_field = NEED_TO_STOCK_FIELD.get(
        new_cluster.need_type.lower(), "tent_count"
    )
    new_required = calculate_required_quantity(
        new_cluster.need_type, new_cluster.total_persons_affected
    )
    available_new_stock = getattr(vehicle, new_stock_field, 0)

    if available_new_stock < new_required:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                f"Aracın yeni küme için yeterli stoku yok. "
                f"Gerekli: {new_required} {new_stock_field}, "
                f"Mevcut: {available_new_stock}"
            ),
        )

    setattr(vehicle, new_stock_field, available_new_stock - new_required)

    vehicle.assigned_cluster_id = new_cluster.id
    new_cluster.status = ClusterStatus.en_route
    new_cluster.assigned_count = new_cluster.request_count
    new_cluster.pending_count = 0

    db.commit()
    db.refresh(vehicle)
    db.refresh(new_cluster)

    return {
        "message": "Araç başarıyla yeni göreve yönlendirildi",
        "vehicle_id": str(vehicle.id),
        "new_cluster_id": str(new_cluster.id),
        "new_cluster_name": new_cluster.cluster_name,
        "old_cluster_id": str(old_cluster.id) if old_cluster else None,
        "old_cluster_status": old_cluster.status if old_cluster else None,
    }


@router.post("/priority-simulate", response_model=schemas.PriorityScenarioResponse)
def simulate_priority_scenario(scenario: schemas.PriorityScenarioRequest):
    """
    Puanlama algoritmasını farklı senaryolarda test eder.

    Örnek senaryo (çadır + soğuk hava + araç yok):
        need_type: "barinma"
        wait_hours: 2
        temperature_celsius: -5
        vehicles_within_radius: 0

    → Beklenen sonuç: temel barınma puanı + 30 (soğuk) + 20 (araç yok) ≈ 100
    """
    pseudo_created_at = datetime.now(timezone.utc) - timedelta(
        hours=max(scenario.wait_hours, 0)
    )
    return calculate_priority_with_context(
        need_type=scenario.need_type,
        created_at=pseudo_created_at,
        temperature_celsius=scenario.temperature_celsius,
        vehicles_within_radius=scenario.vehicles_within_radius,
        is_raining=scenario.is_raining,
        is_night=scenario.is_night,
    )


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
    Bir aracı kümeye atar ve aracı 'yolda' durumuna geçirir.
    Stok burada rezerve edilir (azaltılır), küme 'yolda' statüsüne geçer.
    Görev tamamlandığında /complete endpoint'i çağrılmalıdır.
    """
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster bulunamadı")

    if cluster.status == ClusterStatus.resolved:
        raise HTTPException(status_code=400, detail="Küme zaten çözümlenmiş")

    vehicle = db.query(ReliefVehicle).filter(ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")

    if vehicle.vehicle_status == VehicleStatus.EN_ROUTE and vehicle.assigned_cluster_id != cluster_id:
        raise HTTPException(
            status_code=400,
            detail="Araç zaten başka bir göreve yolda. Önce override ile yönlendirin."
        )

    from services.vehicle_recommendation import calculate_required_quantity
    required_quantity = calculate_required_quantity(
        cluster.need_type,
        cluster.total_persons_affected
    )

    stock_field = NEED_TO_STOCK_FIELD.get(cluster.need_type.lower(), "tent_count")
    available_stock = getattr(vehicle, stock_field, 0)

    if available_stock < required_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Yetersiz stok. Gerekli: {required_quantity}, Mevcut: {available_stock}"
        )

    new_stock = available_stock - required_quantity
    setattr(vehicle, stock_field, new_stock)

    # Yeni akış: küme 'yolda' statüsüne geçer (resolved değil)
    cluster.status = ClusterStatus.en_route
    cluster.assigned_count = cluster.request_count
    cluster.pending_count = 0

    # Araç en_route durumuna geçer ve hangi kümeye gittiği kaydedilir
    vehicle.vehicle_status = VehicleStatus.EN_ROUTE
    vehicle.assigned_cluster_id = cluster.id

    db.commit()
    db.refresh(vehicle)
    db.refresh(cluster)

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
        "message": "Araç görevlendirildi ve yola çıktı",
        "cluster_id": cluster_id,
        "vehicle_id": vehicle_id,
        "remaining_stock": new_stock,
        "distance_km": round(distance_km, 2),
        "eta_minutes": eta_minutes,
        "cluster_status": cluster.status,
        "vehicle_status": vehicle.vehicle_status,
    }


@router.post("/{cluster_id}/complete")
def complete_cluster_mission(cluster_id: UUID, db: Session = Depends(get_db)):
    """Aracın bölgeye ulaştığını ve görevin tamamlandığını işaretler."""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster bulunamadı")

    if cluster.status != ClusterStatus.en_route:
        raise HTTPException(
            status_code=400,
            detail=f"Küme 'yolda' statüsünde değil (mevcut: {cluster.status})"
        )

    # Bu kümeye giden tüm araçları serbest bırak
    en_route_vehicles = (
        db.query(ReliefVehicle)
        .filter(ReliefVehicle.assigned_cluster_id == cluster_id)
        .all()
    )
    for v in en_route_vehicles:
        v.vehicle_status = VehicleStatus.AVAILABLE
        v.assigned_cluster_id = None

    cluster.status = ClusterStatus.resolved
    cluster.resolved_count = cluster.request_count
    cluster.assigned_count = 0

    db.commit()
    db.refresh(cluster)

    return {
        "message": "Görev tamamlandı",
        "cluster_id": cluster_id,
        "released_vehicle_count": len(en_route_vehicles),
        "cluster_status": cluster.status,
    }


