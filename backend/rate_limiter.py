"""
Görev 4.1 — Rate Limiting (Anti-Spam / DDoS Koruması)
Bellekte IP bazlı istek sayacı tutar. DB gerektirmez.
Kural: 1 IP'den 1 dakikada en fazla MAX_REQUESTS kadar istek.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Ayarlar
MAX_REQUESTS = 3       # 1 dakikada maksimum istek sayısı
WINDOW_SECONDS = 60    # Zaman penceresi (saniye)

# Bellek içi sayaç: { "ip": [(timestamp1), (timestamp2), ...] }
_request_log: dict[str, list[float]] = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """
    İstemcinin gerçek IP adresini alır.
    Proxy arkasındaysa X-Forwarded-For header'ına bakar.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def get_client_user_agent(request: Request) -> str:
    """İstemcinin user-agent değerini normalize eder."""
    return (request.headers.get("User-Agent") or "unknown").strip()[:255]


def get_device_key(request: Request) -> str:
    """IP + User-Agent kombinasyonundan kaba bir cihaz anahtarı üretir."""
    return f"{get_client_ip(request)}|{get_client_user_agent(request)}"


def check_rate_limit(request: Request) -> None:
    """
    FastAPI Depends() ile endpoint'lere eklenir.
    Limiti aşan IP'ye 429 Too Many Requests döner.
    """
    ip = get_client_ip(request)
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Zaman penceresi dışındaki eski kayıtları temizle
    _request_log[ip] = [t for t in _request_log[ip] if t > window_start]

    if len(_request_log[ip]) >= MAX_REQUESTS:
        kalan_sure = int(WINDOW_SECONDS - (now - _request_log[ip][0]))
        logger.warning(f"Rate limit asildi: IP={ip} | {len(_request_log[ip])} istek / {WINDOW_SECONDS}sn")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Çok fazla istek gönderildi. Lütfen bekleyin.",
                "limit": MAX_REQUESTS,
                "window_seconds": WINDOW_SECONDS,
                "retry_after_seconds": kalan_sure,
            }
        )

    # Geçerli isteği kaydet
    _request_log[ip].append(now)
    logger.info(f"Rate limit OK: IP={ip} | {len(_request_log[ip])}/{MAX_REQUESTS} istek")
