"""
Görev 4.2 — Saha Ekibi Bildirim Simülasyonu
Gerçek SMS/Email atmaz. Konsola ve log'a yazar.
DB açılınca araç/şoför bilgileri buraya entegre edilir — fonksiyon imzası değişmez.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Simüle edilmiş şoför rehberi
# DB açılınca bu dict yerine veritabanından çekilir
MOCK_DRIVERS = {
    "default": {"name": "Ahmet Yılmaz", "phone": "+90 555 123 4567"},
    "ambulans": {"name": "Mehmet Demir", "phone": "+90 555 234 5678"},
    "itfaiye": {"name": "Ali Kaya",     "phone": "+90 555 345 6789"},
    "kamyon":  {"name": "Hasan Çelik",  "phone": "+90 555 456 7890"},
}


def send_dispatch_notification(
    vehicle_type: str,
    driver_name: str | None,
    destination: str,
    latitude: float,
    longitude: float,
    cargo_summary: str,
    assigned_by: str = "Kriz Merkezi",
) -> dict:
    """
    Araç görevlendirme bildirimi gönderir (simülasyon).

    DB açılınca:
    - driver_name: ReliefVehicle tablosundan çekilir
    - cargo_summary: stok kolonlarından hesaplanır
    """
    driver = MOCK_DRIVERS.get(vehicle_type.lower(), MOCK_DRIVERS["default"])
    name = driver_name or driver["name"]
    phone = driver["phone"]
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    mesaj = (
        f"\n{'='*60}\n"
        f"  📱 SAHA EKİBİ BİLDİRİMİ — {timestamp}\n"
        f"{'='*60}\n"
        f"  Şoför     : {name} ({phone})\n"
        f"  Görev     : {destination} bölgesine teslimat\n"
        f"  Koordinat : {latitude:.4f}, {longitude:.4f}\n"
        f"  Yük       : {cargo_summary}\n"
        f"  Atayan    : {assigned_by}\n"
        f"{'='*60}\n"
    )

    # Konsola yaz (simülasyon)
    print(mesaj)

    # Log'a da yaz
    logger.info(
        f"Bildirim gonderildi | Sofor={name} | Hedef={destination} | "
        f"Koordinat=({latitude},{longitude}) | Yuk={cargo_summary}"
    )

    return {
        "status": "simulated",
        "driver": name,
        "phone": phone,
        "destination": destination,
        "coordinates": {"lat": latitude, "lon": longitude},
        "cargo": cargo_summary,
        "timestamp": timestamp,
    }


def send_assignment_notification(
    cluster_name: str,
    center_lat: float,
    center_lon: float,
    total_persons: int,
    need_type: str,
    vehicle_type: str = "kamyon",
    driver_name: str | None = None,
) -> dict:
    """
    Küme atama bildirimi — assign-vehicle endpoint'i tarafından çağrılır.
    """
    cargo = f"{total_persons} kişi için {need_type} malzemesi"
    return send_dispatch_notification(
        vehicle_type=vehicle_type,
        driver_name=driver_name,
        destination=cluster_name,
        latitude=center_lat,
        longitude=center_lon,
        cargo_summary=cargo,
    )
