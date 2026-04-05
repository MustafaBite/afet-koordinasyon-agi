"""
Coğrafi hesaplamalar için yardımcı fonksiyonlar
"""
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine Formülü ile iki nokta arası mesafe hesaplama (km)
    
    Args:
        lat1: İlk noktanın enlemi
        lon1: İlk noktanın boylamı
        lat2: İkinci noktanın enlemi
        lon2: İkinci noktanın boylamı
    
    Returns:
        Mesafe (kilometre)
    """
    R = 6371  # Dünya yarıçapı (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def is_near_earthquake(lat: float, lon: float, earthquakes: list) -> bool:
    """
    İhbarın deprem bölgesine yakınlığını kontrol eder (50km yarıçap)
    
    Args:
        lat: İhbar noktasının enlemi
        lon: İhbar noktasının boylamı
        earthquakes: Deprem listesi
    
    Returns:
        True eğer 50km içinde deprem varsa
    """
    if not earthquakes:
        return False
    
    for eq in earthquakes:
        eq_lat = eq.get("lat") or eq.get("latitude")
        eq_lon = eq.get("lon") or eq.get("longitude")
        if eq_lat and eq_lon:
            distance = calculate_distance(lat, lon, float(eq_lat), float(eq_lon))
            if distance <= 50:
                return True
    return False
