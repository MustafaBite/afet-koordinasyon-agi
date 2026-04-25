"""
Afet ihbarı oluşturma akışını tekilleştiren servis.

Tüm request giriş noktalarının aynı doğrulama ve kayıt davranışını kullanması
için `main.py` ve `routers/requests.py` tarafından paylaşılır.

Güven Skoru Entegrasyonu:
  Basit binary cross-check yerine üç parametreli güven skoru kullanılır:
  T(r) = 0.60 * S_sismik + 0.25 * S_ip + 0.15 * S_konum
"""
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

import models
import schemas
from live_earthquake_data import get_last_24h_earthquakes
from trust_scorer import calculate_trust_score


@dataclass
class RequestIntakeResult:
    disaster_request: models.DisasterRequest
    is_verified: bool
    trust_score: float = 0.0
    trust_details: dict = field(default_factory=dict)


def create_disaster_request(
    db: Session,
    payload: schemas.RequestCreate,
    *,
    client_ip: str = "unknown",
    created_by_user_id: UUID | None = None,
) -> RequestIntakeResult:
    """
    İhbarı doğrular, güven skoru hesaplar ve veritabanına kaydeder.

    Parametreler:
        db                  : Veritabanı oturumu
        payload             : İhbar verisi (koordinat, ihtiyaç türü vb.)
        client_ip           : İstemci IP adresi (IP analizi için)
        created_by_user_id  : Kimlik doğrulamalı kullanıcı ID'si (opsiyonel)
    """
    earthquakes = get_last_24h_earthquakes()

    # Üç parametreli güven skoru hesapla
    trust = calculate_trust_score(
        lat=payload.latitude,
        lon=payload.longitude,
        ip=client_ip,
        earthquakes=earthquakes,
    )

    db_request = models.DisasterRequest(
        **payload.model_dump(),
        is_verified=trust["is_verified"],
        created_by_user_id=created_by_user_id,
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    return RequestIntakeResult(
        disaster_request=db_request,
        is_verified=trust["is_verified"],
        trust_score=trust["trust_score"],
        trust_details={
            "s_sismik": trust["s_sismik"],
            "s_ip":     trust["s_ip"],
            "s_konum":  trust["s_konum"],
        },
    )
