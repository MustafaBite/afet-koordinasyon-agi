"""
Sprint 6.5 - Bot / anomali tespiti yardimcilari.

Simdilik ayni cihazdan (IP + User-Agent) kisa surede cok sayida farkli
TC kimlik numarasi ile kayit denemelerini bot davranisi olarak isaretler.
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

import models
from rate_limiter import get_client_ip, get_client_user_agent, get_device_key

logger = logging.getLogger("security.anomaly")

REGISTRATION_ANOMALY_THRESHOLD = 10
REGISTRATION_ANOMALY_WINDOW_SECONDS = 10 * 60

_registration_attempts: dict[str, list[dict]] = defaultdict(list)


@dataclass
class DeviceFingerprint:
    device_key: str
    ip_address: str
    user_agent: str


def build_device_fingerprint(request: Request) -> DeviceFingerprint:
    return DeviceFingerprint(
        device_key=get_device_key(request),
        ip_address=get_client_ip(request),
        user_agent=get_client_user_agent(request),
    )


def mask_identifier(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def _trim_attempts(device_key: str, now_ts: float) -> list[dict]:
    window_start = now_ts - REGISTRATION_ANOMALY_WINDOW_SECONDS
    attempts = [
        attempt for attempt in _registration_attempts[device_key]
        if attempt["timestamp"] > window_start
    ]
    _registration_attempts[device_key] = attempts
    return attempts


def record_anomaly_event(
    db: Session,
    request: Request,
    *,
    event_type: str,
    action_taken: str,
    reason: str,
    observed_identifier: str | None = None,
    distinct_value_count: int | None = None,
    window_seconds: int | None = None,
) -> models.AnomalyEvent:
    fingerprint = build_device_fingerprint(request)
    event = models.AnomalyEvent(
        event_type=event_type,
        device_key=fingerprint.device_key,
        ip_address=fingerprint.ip_address,
        user_agent=fingerprint.user_agent,
        request_path=request.url.path,
        action_taken=action_taken,
        reason=reason,
        observed_identifier=mask_identifier(observed_identifier),
        distinct_value_count=distinct_value_count,
        window_seconds=window_seconds,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def guard_against_tc_rotation(
    db: Session,
    request: Request,
    tc_identity_no: str,
) -> None:
    """
    Ayni cihazdan kisa surede cok sayida farkli TC ile kayit denemesi gelirse
    istegi reddeder ve anomaly_events tablosuna yazar.
    """
    fingerprint = build_device_fingerprint(request)
    now_ts = time.time()
    attempts = _trim_attempts(fingerprint.device_key, now_ts)
    attempts.append({
        "timestamp": now_ts,
        "tc_identity_no": tc_identity_no,
    })

    distinct_tcs = {attempt["tc_identity_no"] for attempt in attempts}
    distinct_count = len(distinct_tcs)

    if distinct_count < REGISTRATION_ANOMALY_THRESHOLD:
        logger.info(
            "Registration activity accepted: device=%s distinct_tc=%s",
            fingerprint.device_key,
            distinct_count,
        )
        return

    reason = (
        "Ayni cihazdan kisa surede cok sayida farkli TC kimlik numarasi ile "
        "kayit denemesi algilandi."
    )
    logger.warning(
        "Blocking anomalous registration: device=%s ip=%s distinct_tc=%s path=%s",
        fingerprint.device_key,
        fingerprint.ip_address,
        distinct_count,
        request.url.path,
    )

    try:
        record_anomaly_event(
            db,
            request,
            event_type="register_multi_identity_spike",
            action_taken="blocked",
            reason=reason,
            observed_identifier=tc_identity_no,
            distinct_value_count=distinct_count,
            window_seconds=REGISTRATION_ANOMALY_WINDOW_SECONDS,
        )
    except Exception:
        db.rollback()
        logger.exception("Failed to persist anomaly event")

    raise HTTPException(
        status_code=403,
        detail=(
            "Supheli cihaz davranisi tespit edildi. "
            "Kayit istegi guvenlik nedeniyle reddedildi."
        ),
    )


def reset_anomaly_state() -> None:
    """Testler icin in-memory davranis kaydini temizler."""
    _registration_attempts.clear()
