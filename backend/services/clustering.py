"""
DBSCAN clustering service with graceful degradation under overload.
"""
import logging
from time import perf_counter

import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

import models
from geocoder import reverse_geocode
from models import Cluster, ClusterStatus
from services.priority import calculate_dynamic_priority

logger = logging.getLogger(__name__)

CLUSTER_RADIUS_METERS = 500
EARTH_RADIUS_METERS = 6_371_000
EPS_RADIANS = CLUSTER_RADIUS_METERS / EARTH_RADIUS_METERS
MIN_SAMPLES = 2

DEGRADED_PENDING_THRESHOLD = 100_000
DEGRADED_MAX_PROCESS_SECONDS = 10.0
DEGRADED_MAX_TASK_PACKAGES = 500

PRIORITY_LEVELS = [
    (75, "Kritik"),
    (50, "Yüksek"),
    (25, "Orta"),
    (0, "Düşük"),
]

NEED_TYPE_LABELS = {
    "su": "Su",
    "gida": "Gıda",
    "barinma": "Barınma",
    "medikal": "Medikal",
    "enkaz": "Enkaz Kaldırma",
    "yangin": "Yangın Söndürme",
    "arama_kurtarma": "Arama Kurtarma",
    "is_makinesi": "İş Makinesi",
    "ulasim": "Ulaşım",
}


class DegradationRequired(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _priority_level(score: float) -> str:
    """Öncelik skorunu seviyeye çevirir."""
    for threshold, level in PRIORITY_LEVELS:
        if score >= threshold:
            return level
    return "Düşük"


def _make_cluster_name(need_type: str, location: dict) -> str:
    """Küme için anlamlı isim oluşturur."""
    type_label = NEED_TYPE_LABELS.get(need_type.lower(), need_type.capitalize())
    parts = [p for p in [location.get("district"), location.get("neighborhood")] if p]
    location_str = " ".join(parts) if parts else "Bilinmeyen Bölge"
    return f"{location_str} - {type_label} Kümesi"


def _build_cluster_blueprint(
    *,
    need_type: str,
    cluster_name: str,
    center_latitude: float,
    center_longitude: float,
    location: dict,
    request_count: int,
    total_persons_affected: int,
    average_priority_score: float,
    pending_count: int,
    assigned_count: int,
    resolved_count: int,
    is_noise_cluster: int,
) -> dict:
    return {
        "need_type": need_type,
        "cluster_name": cluster_name,
        "center_latitude": round(center_latitude, 6),
        "center_longitude": round(center_longitude, 6),
        "district": location.get("district"),
        "neighborhood": location.get("neighborhood"),
        "street": location.get("street"),
        "full_address": location.get("full_address"),
        "request_count": request_count,
        "total_persons_affected": total_persons_affected,
        "average_priority_score": round(average_priority_score, 1),
        "priority_level": _priority_level(average_priority_score),
        "pending_count": pending_count,
        "assigned_count": assigned_count,
        "resolved_count": resolved_count,
        "is_noise_cluster": is_noise_cluster,
        "status": ClusterStatus.active,
    }


def _compute_clusters(requests: list, need_type: str) -> list[dict]:
    """
    DBSCAN uygular, ham küme verilerini döndürür (DB'ye yazmaz).
    """
    coords_rad = np.radians([[r.latitude, r.longitude] for r in requests])
    results = []

    if len(requests) < MIN_SAMPLES:
        req = requests[0]
        scores = [calculate_dynamic_priority(req.need_type, req.created_at)]
        location = reverse_geocode(req.latitude, req.longitude)
        results.append({
            "need_type": need_type,
            "cluster_requests": [req],
            "center_lat": req.latitude,
            "center_lon": req.longitude,
            "scores": scores,
            "location": location,
            "is_noise": False,
        })
        return results

    labels = DBSCAN(
        eps=EPS_RADIANS,
        min_samples=MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    ).fit_predict(coords_rad)

    cluster_map: dict[int, list[int]] = {}
    for idx, lbl in enumerate(labels):
        cluster_map.setdefault(lbl, []).append(idx)

    for lbl, indices in cluster_map.items():
        cluster_reqs = [requests[i] for i in indices]
        center_lat = float(np.mean([r.latitude for r in cluster_reqs]))
        center_lon = float(np.mean([r.longitude for r in cluster_reqs]))
        scores = [calculate_dynamic_priority(r.need_type, r.created_at) for r in cluster_reqs]
        location = reverse_geocode(center_lat, center_lon)
        results.append({
            "need_type": need_type,
            "cluster_requests": cluster_reqs,
            "center_lat": center_lat,
            "center_lon": center_lon,
            "scores": scores,
            "location": location,
            "is_noise": lbl == -1,
        })

    return results


def _build_standard_cluster_blueprints(
    all_requests: list[models.DisasterRequest],
) -> list[dict]:
    started_at = perf_counter()
    groups: dict[str, list] = {}
    for req in all_requests:
        groups.setdefault(req.need_type.lower(), []).append(req)

    blueprints = []
    for need_type, requests in groups.items():
        if perf_counter() - started_at > DEGRADED_MAX_PROCESS_SECONDS:
            raise DegradationRequired("DBSCAN processing exceeded the safe time budget.")

        raw_clusters = _compute_clusters(requests, need_type)
        if perf_counter() - started_at > DEGRADED_MAX_PROCESS_SECONDS:
            raise DegradationRequired("DBSCAN processing exceeded the safe time budget.")

        for cluster_data in raw_clusters:
            avg_score = sum(cluster_data["scores"]) / len(cluster_data["scores"])
            location = cluster_data["location"]
            cluster_name = _make_cluster_name(need_type, location)
            if cluster_data["is_noise"]:
                cluster_name = f"{cluster_name} (Dağınık)"

            status_counts = {"pending": 0, "assigned": 0, "resolved": 0}
            for req in cluster_data["cluster_requests"]:
                status_counts[req.status.value] += 1

            blueprints.append(
                _build_cluster_blueprint(
                    need_type=need_type,
                    cluster_name=cluster_name,
                    center_latitude=cluster_data["center_lat"],
                    center_longitude=cluster_data["center_lon"],
                    location=location,
                    request_count=len(cluster_data["cluster_requests"]),
                    total_persons_affected=sum(
                        req.person_count for req in cluster_data["cluster_requests"]
                    ),
                    average_priority_score=avg_score,
                    pending_count=status_counts["pending"],
                    assigned_count=status_counts["assigned"],
                    resolved_count=status_counts["resolved"],
                    is_noise_cluster=int(cluster_data["is_noise"]),
                )
            )

            if perf_counter() - started_at > DEGRADED_MAX_PROCESS_SECONDS:
                raise DegradationRequired("Cluster generation exceeded the safe time budget.")

    return blueprints


def _build_degraded_cluster_blueprints(
    all_requests: list[models.DisasterRequest],
) -> list[dict]:
    prioritized_requests = sorted(
        all_requests,
        key=lambda req: (
            -calculate_dynamic_priority(req.need_type, req.created_at),
            req.created_at,
        ),
    )

    selected_requests = prioritized_requests[:DEGRADED_MAX_TASK_PACKAGES]
    omitted_count = max(len(prioritized_requests) - len(selected_requests), 0)

    logger.warning(
        "Graceful degradation active: total_pending=%s selected=%s omitted=%s",
        len(all_requests),
        len(selected_requests),
        omitted_count,
    )

    blueprints = []
    for index, req in enumerate(selected_requests, start=1):
        score = calculate_dynamic_priority(req.need_type, req.created_at)
        type_label = NEED_TYPE_LABELS.get(req.need_type.lower(), req.need_type.capitalize())
        blueprints.append(
            _build_cluster_blueprint(
                need_type=req.need_type.lower(),
                cluster_name=f"Hızlı Görev Paketi #{index} - {type_label}",
                center_latitude=req.latitude,
                center_longitude=req.longitude,
                location={},
                request_count=1,
                total_persons_affected=req.person_count,
                average_priority_score=score,
                pending_count=1,
                assigned_count=0,
                resolved_count=0,
                is_noise_cluster=0,
            )
        )

    return blueprints


def _persist_cluster_blueprints(db: Session, blueprints: list[dict]) -> list[Cluster]:
    db.query(Cluster).filter(Cluster.status == ClusterStatus.active).delete()

    if not blueprints:
        db.commit()
        return []

    clusters = []
    for blueprint in blueprints:
        cluster = Cluster(**blueprint)
        db.add(cluster)
        clusters.append(cluster)

    db.commit()
    for cluster in clusters:
        db.refresh(cluster)

    return sorted(clusters, key=lambda cluster: -cluster.average_priority_score)


def run_clustering(db: Session) -> list[Cluster]:
    """
    Tüm talepleri kümeler, sonuçları DB'ye yazar.
    Mevcut aktif kümeler silinir, yenileri oluşturulur.
    """
    all_requests = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.status == models.RequestStatus.pending
    ).all()

    if not all_requests:
        db.query(Cluster).filter(Cluster.status == ClusterStatus.active).delete()
        db.commit()
        return []

    if len(all_requests) >= DEGRADED_PENDING_THRESHOLD:
        reason = (
            "Pending request threshold exceeded; falling back to urgent task packages."
        )
        logger.warning(reason)
        return _persist_cluster_blueprints(
            db,
            _build_degraded_cluster_blueprints(all_requests),
        )

    try:
        blueprints = _build_standard_cluster_blueprints(all_requests)
    except DegradationRequired as exc:
        logger.warning("Clustering degraded: %s", exc.reason)
        blueprints = _build_degraded_cluster_blueprints(all_requests)

    return _persist_cluster_blueprints(db, blueprints)
