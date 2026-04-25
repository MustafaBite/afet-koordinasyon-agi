from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Cluster, ClusterStatus, DisasterRequest, RequestStatus
from services import clustering

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _pending_request(need_type: str, minutes_ago: int, person_count: int = 1) -> DisasterRequest:
    created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return DisasterRequest(
        id=uuid4(),
        latitude=41.0 + (minutes_ago / 1000),
        longitude=29.0 + (minutes_ago / 1000),
        need_type=need_type,
        person_count=person_count,
        description=f"{need_type} request",
        status=RequestStatus.pending,
        created_at=created_at,
        is_verified=True,
    )


def test_run_clustering_uses_degraded_mode_when_pending_threshold_exceeded(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    monkeypatch.setattr(clustering, "DEGRADED_PENDING_THRESHOLD", 3)
    monkeypatch.setattr(clustering, "DEGRADED_MAX_TASK_PACKAGES", 2)

    old_cluster = Cluster(
        id=uuid4(),
        need_type="gida",
        cluster_name="Old Active Cluster",
        center_latitude=41.0,
        center_longitude=29.0,
        request_count=5,
        total_persons_affected=20,
        average_priority_score=10.0,
        priority_level="Dusuk",
        pending_count=5,
        assigned_count=0,
        resolved_count=0,
        is_noise_cluster=0,
        status=ClusterStatus.active,
    )
    db.add(old_cluster)
    db.add_all(
        [
            _pending_request("medikal", minutes_ago=1, person_count=2),
            _pending_request("arama_kurtarma", minutes_ago=2, person_count=4),
            _pending_request("gida", minutes_ago=3, person_count=1),
            _pending_request("su", minutes_ago=4, person_count=3),
        ]
    )
    db.commit()

    try:
        clusters = clustering.run_clustering(db)

        assert len(clusters) == 2
        assert all("Hızlı Görev Paketi" in cluster.cluster_name for cluster in clusters)
        assert all(cluster.request_count == 1 for cluster in clusters)
        assert db.query(Cluster).filter(Cluster.cluster_name == "Old Active Cluster").count() == 0
        assert clusters[0].average_priority_score >= clusters[1].average_priority_score
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_run_clustering_falls_back_when_processing_time_budget_is_exceeded(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    monkeypatch.setattr(clustering, "DEGRADED_PENDING_THRESHOLD", 100)
    monkeypatch.setattr(clustering, "DEGRADED_MAX_PROCESS_SECONDS", 0)
    monkeypatch.setattr(clustering, "DEGRADED_MAX_TASK_PACKAGES", 5)

    db.add_all(
        [
            _pending_request("medikal", minutes_ago=1, person_count=2),
            _pending_request("gida", minutes_ago=20, person_count=1),
        ]
    )
    db.commit()

    try:
        clusters = clustering.run_clustering(db)

        assert len(clusters) == 2
        assert all(cluster.status == ClusterStatus.active for cluster in clusters)
        assert all("Hızlı Görev Paketi" in cluster.cluster_name for cluster in clusters)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
