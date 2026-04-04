"""
Akıllı Araç Önerisi Motoru
Çok kriterli karar verme (MCDM) ile en uygun aracı seçer
"""
import math
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from models import ReliefVehicle, Cluster


# Araç tipi - hız eşleştirmesi (araştırmadan)
VEHICLE_SPEEDS = {
    "Ambulans": 70,
    "Kamyon": 60,
    "İtfaiye": 65,
    "Su Tankeri": 55,
    "İş Makinesi": 30,
}

# İhtiyaç tipi - stok alanı eşleştirmesi
NEED_TO_STOCK_FIELD = {
    "barinma": "tent_count",
    "gida": "food_count",
    "su": "water_count",
    "medikal": "medical_count",
    "enkaz": "blanket_count",
    "yangin": "water_count",
    "arama_kurtarma": "medical_count",
}

# Kişi başı ihtiyaç hesaplama (Sphere standartları)
NEED_PER_PERSON = {
    "barinma": 0.25,      # 1 çadır = 4 kişi
    "gida": 1.0,          # 1 paket = 1 kişi
    "su": 20.0,           # 20 litre/kişi
    "medikal": 0.1,       # 1 kit = 10 kişi
    "enkaz": 0.05,        # Ekipman ihtiyacı
    "yangin": 50.0,       # Su ihtiyacı (litre)
    "arama_kurtarma": 0.2,
}

# MCDM Ağırlıkları (araştırmadan optimize edilmiş)
WEIGHTS = {
    "urgency": 0.40,      # Aciliyet
    "distance": 0.27,     # Mesafe (ETA)
    "stock": 0.18,        # Stok yeterliliği
    "speed": 0.15,        # Araç hızı
}

# Afet koşulları düzeltme katsayısı
DISASTER_CONDITION_FACTOR = 1.2


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki nokta arası kuş uçuşu mesafe (km)
    Haversine formülü
    """
    R = 6371  # Dünya yarıçapı (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_eta(distance_km: float, vehicle_speed: int, priority_score: float) -> int:
    """
    Tahmini varış süresi (dakika)
    Yüksek aciliyet durumlarında hız artışı uygulanır
    """
    speed = vehicle_speed
    
    # Kritik durumlarda hız %10 artırılır
    if priority_score >= 75:
        speed *= 1.1
    
    # Afet koşulları düzeltmesi
    adjusted_distance = distance_km * DISASTER_CONDITION_FACTOR
    
    eta_hours = adjusted_distance / speed
    eta_minutes = int(eta_hours * 60)
    
    return max(eta_minutes, 1)  # Minimum 1 dakika


def calculate_required_quantity(need_type: str, person_count: int) -> int:
    """
    Sphere standartlarına göre gerekli malzeme miktarı
    """
    per_person = NEED_PER_PERSON.get(need_type.lower(), 1.0)
    return math.ceil(person_count * per_person)


def get_vehicle_stock(vehicle: ReliefVehicle, need_type: str) -> int:
    """
    Aracın belirli bir ihtiyaç tipi için mevcut stoğu
    """
    stock_field = NEED_TO_STOCK_FIELD.get(need_type.lower(), "tent_count")
    return getattr(vehicle, stock_field, 0)


def calculate_vehicle_score(
    vehicle: ReliefVehicle,
    cluster: Cluster,
    required_quantity: int,
    all_vehicles: List[ReliefVehicle]
) -> Tuple[float, Dict]:
    """
    Çok kriterli skorlama (MCDM)
    Returns: (total_score, details_dict)
    """
    # Mesafe hesapla
    distance_km = calculate_haversine_distance(
        vehicle.latitude, vehicle.longitude,
        cluster.center_latitude, cluster.center_longitude
    )
    
    # Araç stoğu
    available_stock = get_vehicle_stock(vehicle, cluster.need_type)
    
    # Araç hızı
    vehicle_speed = vehicle.base_speed_kmh or VEHICLE_SPEEDS.get(vehicle.vehicle_type, 60)
    
    # ETA hesapla
    eta_minutes = calculate_eta(distance_km, vehicle_speed, cluster.average_priority_score)
    
    # --- SKORLAMA ---
    
    # 1. Stok Skoru (0-100)
    if available_stock < required_quantity:
        stock_score = 0  # Yeterli stok yok, elenir
    else:
        # Fazla stok = daha yüksek skor
        stock_ratio = min(available_stock / required_quantity, 2.0)
        stock_score = stock_ratio * 50  # Max 100
    
    # 2. Mesafe Skoru (0-100) - Yakın = Yüksek
    max_distance = max([calculate_haversine_distance(
        v.latitude, v.longitude,
        cluster.center_latitude, cluster.center_longitude
    ) for v in all_vehicles] + [1])
    
    distance_score = 100 - (distance_km / max_distance * 100)
    distance_score = max(distance_score, 0)
    
    # 3. Hız Skoru (0-100)
    max_speed = max([v.base_speed_kmh or 60 for v in all_vehicles] + [60])
    speed_score = (vehicle_speed / max_speed) * 100
    
    # 4. Aciliyet Skoru (0-100) - Cluster'ın priority score'u
    urgency_score = cluster.average_priority_score
    
    # Ağırlıklı toplam skor
    total_score = (
        urgency_score * WEIGHTS["urgency"] +
        distance_score * WEIGHTS["distance"] +
        stock_score * WEIGHTS["stock"] +
        speed_score * WEIGHTS["speed"]
    )
    
    details = {
        "distance_km": round(distance_km, 2),
        "eta_minutes": eta_minutes,
        "available_stock": available_stock,
        "required_quantity": required_quantity,
        "stock_score": round(stock_score, 1),
        "distance_score": round(distance_score, 1),
        "speed_score": round(speed_score, 1),
        "urgency_score": round(urgency_score, 1),
        "total_score": round(total_score, 1),
    }
    
    return total_score, details


def recommend_vehicles(db: Session, cluster_id: str, top_n: int = 3) -> List[Dict]:
    """
    Bir cluster için en uygun araçları önerir
    
    Args:
        db: Database session
        cluster_id: Cluster UUID
        top_n: Kaç araç önerilecek (default: 3)
    
    Returns:
        List of recommended vehicles with scores and details
    """
    from models import Cluster
    from uuid import UUID
    
    # Cluster bilgisini al
    cluster = db.query(Cluster).filter(Cluster.id == UUID(cluster_id)).first()
    if not cluster:
        return []
    
    # Gerekli malzeme miktarını hesapla
    required_quantity = calculate_required_quantity(
        cluster.need_type,
        cluster.total_persons_affected
    )
    
    # Tüm araçları al
    all_vehicles = db.query(ReliefVehicle).all()
    if not all_vehicles:
        return []
    
    # Her araç için skor hesapla
    scored_vehicles = []
    for vehicle in all_vehicles:
        score, details = calculate_vehicle_score(
            vehicle, cluster, required_quantity, all_vehicles
        )
        
        # Stok yetersizse eleme
        if details["stock_score"] == 0:
            continue
        
        scored_vehicles.append({
            "vehicle": vehicle,
            "score": score,
            "details": details
        })
    
    # Skora göre sırala (en yüksek önce)
    scored_vehicles.sort(key=lambda x: x["score"], reverse=True)
    
    # Top N'i döndür
    return scored_vehicles[:top_n]
