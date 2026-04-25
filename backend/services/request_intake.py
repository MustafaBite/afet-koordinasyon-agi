"""
Afet ihbari olusturma akisini tekilleştiren servis.

Tum request giris noktalarinin ayni dogrulama ve kayit davranisini kullanmasi
icin `main.py` ve `routers/requests.py` tarafindan paylasilir.
"""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

import models
import schemas
from live_earthquake_data import get_last_24h_earthquakes
from utils.geo import is_near_earthquake


@dataclass
class RequestIntakeResult:
    disaster_request: models.DisasterRequest
    is_verified: bool


def determine_request_verification(payload: schemas.RequestCreate) -> bool:
    earthquakes = get_last_24h_earthquakes()
    return is_near_earthquake(payload.latitude, payload.longitude, earthquakes)


def create_disaster_request(
    db: Session,
    payload: schemas.RequestCreate,
    *,
    created_by_user_id: UUID | None = None,
) -> RequestIntakeResult:
    verified = determine_request_verification(payload)
    db_request = models.DisasterRequest(
        **payload.model_dump(),
        is_verified=verified,
        created_by_user_id=created_by_user_id,
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return RequestIntakeResult(disaster_request=db_request, is_verified=verified)
