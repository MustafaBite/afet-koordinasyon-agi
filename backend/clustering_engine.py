import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

import models
from models import Cluster, ClusterStatus
from priority_engine import calculate_dynamic_priority
from geocoder import reverse_geocode

CLUSTER_RADIUS_METERS = 500
EARTH_RADIUS_METERS = 6_371_000
EPS_RADIANS = CLUSTER_RADIUS_METERS / EARTH_RADIUS_METERS
MIN_SAMPLES = 2

PRIORITY_LEVELS = [
    (75, "Kritik"),
    (50, "Yüksek"),
    (25, "Orta"),
    (0,  "Düşük"),
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


def _priority_level(score: float) -> str:
    for threshold, level in PRIORITY_LEVELS:
        if score >= threshold:
            return level
    return "Düşük"


def _make_cluster_name(need_type: str, location: dict) -> str:
    type_label = NEED_TYPE_LABELS.get(need_type.lower(), need_type.capitalize())
    parts = [p for p in [location.get("district"), location.get("neighborhood")] if p]
    location_str = " ".join(parts) if parts else "Bilinmeyen Bölge"
    return f"{location_str} - {type_label} Kümesi"


def _compute_clusters(requests: list, need_type: str) -> list[dict]:
    """DBSCAN uygular, ham küme verilerini döndürür (DB'ye yazmaz)."""
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


def run_clustering(db: Session) -> list[Cluster]:
    """
    Tüm talepleri kümeler, sonuçları DB'ye yazar.
    Mevcut aktif kümeler silinir, yenileri oluşturulur.
    """
    all_requests = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.status == models.RequestStatus.pending
    ).all()

    # Mevcut aktif kümeleri temizle
    db.query(Cluster).filter(Cluster.status == ClusterStatus.active).delete()

    if not all_requests:
        db.commit()
        return []

    groups: dict[str, list] = {}
    for req in all_requests:
        groups.setdefault(req.need_type.lower(), []).append(req)

    new_clusters = []

    for need_type, requests in groups.items():
        for c in _compute_clusters(requests, need_type):
            avg_score = round(sum(c["scores"]) / len(c["scores"]), 1)
            loc = c["location"]
            name = _make_cluster_name(need_type, loc)
            if c["is_noise"]:
                name = f"{name} (Dağınık)"

            status_counts = {"pending": 0, "assigned": 0, "resolved": 0}
            for r in c["cluster_requests"]:
                status_counts[r.status.value] += 1

            cluster = Cluster(
                need_type=need_type,
                cluster_name=name,
                center_latitude=round(c["center_lat"], 6),
                center_longitude=round(c["center_lon"], 6),
                district=loc.get("district"),
                neighborhood=loc.get("neighborhood"),
                street=loc.get("street"),
                full_address=loc.get("full_address"),
                request_count=len(c["cluster_requests"]),
                total_persons_affected=sum(r.person_count for r in c["cluster_requests"]),
                average_priority_score=avg_score,
                priority_level=_priority_level(avg_score),
                pending_count=status_counts["pending"],
                assigned_count=status_counts["assigned"],
                resolved_count=status_counts["resolved"],
                is_noise_cluster=int(c["is_noise"]),
                status=ClusterStatus.active,
            )
            db.add(cluster)
            new_clusters.append(cluster)

    db.commit()
    for c in new_clusters:
        db.refresh(c)

    return sorted(new_clusters, key=lambda c: -c.average_priority_score)
