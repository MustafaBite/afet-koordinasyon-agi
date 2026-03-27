from functools import lru_cache
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent="afet-koordinasyon-agi/1.0", timeout=5)
_reverse = RateLimiter(_geolocator.reverse, min_delay_seconds=1.1, max_retries=1)

_PRECISION = 2


@lru_cache(maxsize=4096)
def _cached_reverse(lat: float, lon: float) -> dict | None:
    try:
        result = _reverse(f"{lat}, {lon}", language="tr", exactly_one=True)
        if result and result.raw and "address" in result.raw:
            return result.raw["address"]
    except Exception as e:
        print(f"[geocoder] reverse failed ({lat}, {lon}): {e}")
    return None


def reverse_geocode(lat: float, lon: float) -> dict:
    address = _cached_reverse(round(lat, _PRECISION), round(lon, _PRECISION))

    result = {"district": None, "neighborhood": None, "street": None, "full_address": None}

    if not address:
        return result

    result["district"] = (
        address.get("town")
        or address.get("county")
        or address.get("city_district")
        or address.get("suburb")
    )
    result["neighborhood"] = (
        address.get("neighbourhood")
        or address.get("quarter")
        or address.get("suburb")
    )
    result["street"] = (
        address.get("road")
        or address.get("pedestrian")
        or address.get("footway")
    )

    parts = [p for p in [result["street"], result["neighborhood"], result["district"]] if p]
    result["full_address"] = ", ".join(parts) if parts else address.get("display_name")

    return result
