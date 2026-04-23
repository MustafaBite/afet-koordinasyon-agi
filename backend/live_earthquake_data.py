import requests
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── TTL Cache ──────────────────────────────────────────────────────────────
# Kandilli API'ye her ihbarda istek atmak yerine sonucu 60 saniye boyunca
# bellekte tutuyoruz. Bu sayede 500 eş zamanlı kullanıcı geldiğinde
# hepsi aynı dış API çağrısını beklemek yerine bellekten okur.
CACHE_TTL_SECONDS = 60  # Kaç saniyede bir Kandilli'ye gerçek istek atılır

_last_known_cache: list = []
_cache_timestamp: float = 0.0   # Son başarılı çekimin unix timestamp'i


def get_last_24h_earthquakes() -> list:
    """
    Kandilli API'den son 24 saatin deprem verilerini çeker.

    Performans İyileştirmesi (v2):
    - Sonuçlar 60 saniye boyunca bellekte tutulur (TTL cache).
    - Aynı 60 saniyelik pencerede gelen tüm istekler API'ye gitmez,
      bellekten okur. Bu, yüksek yük altında dış API bağımlılığını ortadan kaldırır.
    - API çökerse son bilinen cache döner (fallback).
    - 5.0+ büyüklüğündeki depremler is_major=True olarak işaretlenir.
    """
    global _last_known_cache, _cache_timestamp

    now = time.time()

    # Cache geçerliyse direkt dön — Kandilli'ye istek atma
    if _last_known_cache and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        logger.debug(f"Cache hit — Kandilli API atlandı ({int(now - _cache_timestamp)}s önce güncellendi)")
        return _last_known_cache

    # Cache süresi dolmuş veya ilk çalışma — Kandilli'ye git
    url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.warning("Kandilli API zaman aşımı — son bilinen veri kullanılıyor.")
        return _last_known_cache
    except requests.exceptions.ConnectionError:
        logger.warning("Kandilli API bağlantı hatası — son bilinen veri kullanılıyor.")
        return _last_known_cache
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Kandilli API HTTP hatası ({e}) — son bilinen veri kullanılıyor.")
        return _last_known_cache
    except Exception as e:
        logger.warning(f"Kandilli API beklenmeyen hata ({e}) — son bilinen veri kullanılıyor.")
        return _last_known_cache

    earthquakes = []

    for eq in data.get("result", []):
        time_str = eq.get("date_time") or eq.get("date")
        if not time_str:
            continue

        try:
            eq_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        if eq_time <= datetime.now() - timedelta(hours=24):
            continue

        coords = eq.get("geojson", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        mag = None
        try:
            mag = float(eq.get("mag") or eq.get("magnitude") or 0)
        except (TypeError, ValueError):
            mag = 0.0

        earthquakes.append({
            "lat": float(coords[1]),
            "lon": float(coords[0]),
            "mag": mag,
            "title": eq.get("title", ""),
            "date_time": time_str,
            "is_major": mag >= 5.0,
        })

    # Büyük depremler (5.0+) önce, sonra tarihe göre yeniden eskiye
    earthquakes.sort(key=lambda x: (not x["is_major"], x["date_time"]), reverse=False)

    # Cache'i güncelle
    if earthquakes:
        _last_known_cache = earthquakes
        _cache_timestamp = now
        logger.info(
            f"Kandilli cache güncellendi: {len(earthquakes)} deprem, "
            f"{sum(1 for e in earthquakes if e['is_major'])} tanesi büyük (5.0+)."
        )

    return earthquakes


def get_major_earthquakes_last_3_months() -> list:
    """
    USGS API'den son 3 ayda Türkiye'de gerçekleşen 5.0+ büyüklüğündeki depremleri çeker.
    En yeniden eskiye sıralı döner.
    API çökerse boş liste döner, uygulama çökmez.
    """
    from datetime import timezone
    from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        f"?format=geojson"
        f"&starttime={from_date}&endtime={to_date}"
        f"&minmagnitude=5.0"
        f"&minlatitude=36&maxlatitude=42"
        f"&minlongitude=26&maxlongitude=45"
        f"&orderby=time"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.warning("USGS API zaman aşımı.")
        return []
    except requests.exceptions.ConnectionError:
        logger.warning("USGS API bağlantı hatası.")
        return []
    except Exception as e:
        logger.warning(f"USGS API beklenmeyen hata: {e}")
        return []

    results = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        ts_ms = props.get("time")
        eq_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts_ms else ""

        results.append({
            "lat": float(coords[1]),
            "lon": float(coords[0]),
            "mag": float(props.get("mag") or 0),
            "title": props.get("place", ""),
            "date_time": eq_time,
            "is_major": True,
            "source": "usgs",
        })

    logger.info(f"Son 3 ayda 5.0+ deprem: {len(results)} adet (USGS)")
    return results
