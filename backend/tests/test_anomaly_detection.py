from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import AnomalyEvent, Base
from routers import auth
from services.anomaly_detection import reset_anomaly_state

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _build_register_payload(index: int) -> dict:
    return {
        "email": f"bot-{index}@test.com",
        "password": "Test123!",
        "first_name": "Bot",
        "last_name": f"User{index}",
        "tc_identity_no": f"{index:011d}",
        "phone": f"05{index:09d}"[-11:],
        "role": "citizen",
        "expertise_area": None,
        "organization": None,
        "city": "Ankara",
        "district": "Cankaya",
        "profile_photo_url": None,
    }


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    return app


def test_register_blocks_tc_rotation_and_logs_event():
    Base.metadata.create_all(bind=engine)
    reset_anomaly_state()

    app = _build_test_app()
    client = TestClient(app)
    headers = {"User-Agent": "pytest-bot"}

    try:
        for index in range(1, 10):
            response = client.post(
                "/auth/register",
                json=_build_register_payload(index),
                headers=headers,
            )
            assert response.status_code == 201

        blocked_response = client.post(
            "/auth/register",
            json=_build_register_payload(10),
            headers=headers,
        )

        assert blocked_response.status_code == 403
        assert "Supheli cihaz davranisi" in blocked_response.json()["detail"]

        db = TestingSessionLocal()
        try:
            events = db.query(AnomalyEvent).all()
            assert len(events) == 1

            event = events[0]
            assert event.event_type == "register_multi_identity_spike"
            assert event.action_taken == "blocked"
            assert event.distinct_value_count == 10
            assert event.request_path == "/auth/register"
            assert event.observed_identifier != _build_register_payload(10)["tc_identity_no"]
        finally:
            db.close()
    finally:
        client.close()
        app.dependency_overrides.clear()
        reset_anomaly_state()
        Base.metadata.drop_all(bind=engine)
