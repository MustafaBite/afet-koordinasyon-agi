from fastapi import FastAPI, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from math import sqrt
import asyncio

from database import engine
from rate_limiter import check_rate_limit
from notification_service import send_assignment_notification
from live_earthquake_data import get_last_24h_earthquakes, get_major_earthquakes_last_3_months
import models
import schemas

# Geo yardımcıları — utils varsa oradan, yoksa local tanımla
try:
    from utils.geo import calculate_distance, is_near_earthquake
    from utils.websocket import ConnectionManager
    from services.priority import calculate_dynamic_priority
    from core.dependencies import get_db as _get_db
    def get_db():
        yield from _get_db()
except ImportError:
    import math

    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def is_near_earthquake(lat, lon, earthquakes):
        if not earthquakes:
            return False
        for eq in earthquakes:
            eq_lat = eq.get("lat") or eq.get("latitude")
            eq_lon = eq.get("lon") or eq.get("longitude")
            if eq_lat and eq_lon:
                if calculate_distance(lat, lon, float(eq_lat), float(eq_lon)) <= 50:
                    return True
        return False

    from priority_engine import calculate_dynamic_priority
    from database import SessionLocal

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    class ConnectionManager:
        def __init__(self):
            self.active_connections: list[WebSocket] = []
        async def connect(self, ws: WebSocket):
            await ws.accept()
            self.active_connections.append(ws)
        def disconnect(self, ws: WebSocket):
            self.active_connections.remove(ws)
        async def broadcast(self, data: dict):
            for conn in self.active_connections:
                try:
                    await conn.send_json(data)
                except Exception:
                    pass

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# ── Swagger / OpenAPI metadata ─────────────────────────────────────────────
app = FastAPI(
    title="RESQ — Afet Koordinasyon API",
    version="1.0.0",
    description="""
## RESQ Afet Koordinasyon Sistemi — Backend API

Bu API, deprem ve diğer afet durumlarında gelen yardım ihbarlarını yönetir,
önceliklendirir ve saha ekiplerine koordineli biçimde iletir.

### Temel Özellikler
- **Sabotaj Engeli (Cross-Check):** Gelen her ihbar, Kandilli Rasathanesi'nin anlık deprem
  verileriyle karşılaştırılır. Deprem bölgesi dışından gelen ihbarlar otomatik olarak
  `is_verified=False` (şüpheli) olarak işaretlenir.
- **Dinamik Önceliklendirme:** Her ihbar, ihtiyaç türü ve bekleme süresine göre
  0–100 arası bir aciliyet puanı alır. Puan zamanla artar (queue starvation önleme).
- **Rate Limiting:** Aynı IP'den 1 dakikada en fazla 3 ihbar gönderilebilir (DDoS koruması).
- **Kümeleme (DBSCAN):** Birbirine yakın ihbarlar coğrafi olarak gruplanır ve
  görev paketleri oluşturulur.
- **Gerçek Zamanlı Bildirim:** WebSocket üzerinden bağlı tüm istemcilere anlık güncelleme iletilir.
""",
    contact={
        "name": "RESQ Geliştirme Ekibi",
    },
    tags_metadata=[
        {"name": "Sistem", "description": "API sağlık kontrolü ve genel bilgi endpoint'leri."},
        {"name": "İhbar Yönetimi", "description": "Afet ihbarlarını oluşturma, listeleme ve durum güncelleme işlemleri."},
        {"name": "Araç Yönetimi", "description": "Yardım araçlarını kaydetme, listeleme ve stok güncelleme işlemleri."},
        {"name": "Deprem Verileri", "description": "Kandilli ve USGS kaynaklı anlık deprem verilerine erişim."},
        {"name": "Operasyon", "description": "Sürü operasyonu ve WebSocket tabanlı gerçek zamanlı iletişim."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
try:
    from routers import requests as requests_router, clusters as clusters_router, auth as auth_router, vehicles as vehicles_router
    app.include_router(auth_router.router)
    app.include_router(clusters_router.router)   # /requests/task-packages — önce ekle
    app.include_router(requests_router.router, prefix="/api/ihbarlar")
    app.include_router(vehicles_router.router)
except Exception as e:
    print(f"ROUTER HATASI: {e}")

manager = ConnectionManager()

# ── SISTEM ────────────────────────────────────────────────────────────────

@app.get(
    "/",
    tags=["Sistem"],
    summary="API Kök Endpoint",
    description="API'nin çalışıp çalışmadığını kontrol eder. Basit bir karşılama mesajı döner.",
)
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}


@app.get(
    "/health",
    tags=["Sistem"],
    summary="Sağlık Kontrolü",
    description="Sistemin ayakta olup olmadığını kontrol eder. Load balancer ve monitoring araçları tarafından kullanılır.",
)
def health_check():
    return {"status": "ok", "message": "Afet Koordinasyon API çalışıyor"}


# ── İHBAR YÖNETİMİ ────────────────────────────────────────────────────────

@app.post(
    "/talep-gonder",
    response_model=schemas.RequestResponse,
    tags=["İhbar Yönetimi"],
    summary="Yeni Afet İhbarı Gönder (Eski Endpoint)",
    description="""
Yeni bir afet yardım talebi oluşturur.

**Sabotaj Engeli (Cross-Check):**
Gönderilen koordinat, Kandilli Rasathanesi'nin son 24 saatteki deprem verileriyle
karşılaştırılır. İhbar, herhangi bir deprem merkezine 50 km'den yakınsa
`is_verified=True` (doğrulandı), uzaksa `is_verified=False` (şüpheli) olarak işaretlenir.

**Rate Limiting:**
Aynı IP adresinden 1 dakika içinde en fazla 3 istek gönderilebilir.
Limit aşılırsa HTTP 429 döner.

> Bu endpoint geriye dönük uyumluluk için korunmaktadır. Yeni entegrasyonlar için `/requests` kullanın.
""",
)
def create_request_legacy(
    request_data: schemas.RequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit),
):
    return _create_request_sync(request_data, db)


@app.post(
    "/requests",
    tags=["İhbar Yönetimi"],
    summary="Yeni Afet İhbarı Gönder (Yeni Endpoint)",
    description="""
Yeni bir afet yardım talebi oluşturur ve WebSocket üzerinden bağlı tüm istemcilere
anlık bildirim gönderir.

**Sabotaj Engeli (Cross-Check):**
Gönderilen koordinat, Kandilli Rasathanesi'nin son 24 saatteki deprem verileriyle
karşılaştırılır. İhbar, herhangi bir deprem merkezine 50 km'den yakınsa
`is_verified=True` (doğrulandı), uzaksa `is_verified=False` (şüpheli) olarak işaretlenir.

**Rate Limiting:**
Aynı IP adresinden 1 dakika içinde en fazla 3 istek gönderilebilir.
Limit aşılırsa HTTP 429 döner.

**WebSocket Bildirimi:**
İhbar kaydedildikten sonra `/ws` kanalına bağlı tüm istemcilere `NEW_REQUEST` eventi iletilir.
""",
)
async def create_request(
    request_data: schemas.RequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit),
):
    earthquakes = get_last_24h_earthquakes()
    verified = is_near_earthquake(request_data.latitude, request_data.longitude, earthquakes)
    db_request = models.DisasterRequest(**request_data.model_dump(), is_verified=verified)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    await manager.broadcast({
        "event": "NEW_REQUEST",
        "data": {
            "id": str(db_request.id),
            "need_type": db_request.need_type,
            "latitude": db_request.latitude,
            "longitude": db_request.longitude,
            "is_verified": verified,
        }
    })
    return db_request


def _create_request_sync(request_data: schemas.RequestCreate, db: Session):
    earthquakes = get_last_24h_earthquakes()
    verified = is_near_earthquake(request_data.latitude, request_data.longitude, earthquakes)
    db_request = models.DisasterRequest(**request_data.model_dump(), is_verified=verified)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@app.get(
    "/talepler/oncelikli",
    response_model=List[schemas.PrioritizedRequestResponse],
    tags=["İhbar Yönetimi"],
    summary="Öncelikli İhbarları Listele (Eski Endpoint)",
    description="""
Tüm ihbarları dinamik öncelik puanına göre sıralı döner.

> Bu endpoint geriye dönük uyumluluk için korunmaktadır. Yeni entegrasyonlar için `/requests/prioritized` kullanın.
""",
)
def get_prioritized_requests_legacy(db: Session = Depends(get_db)):
    return _get_prioritized(db)


@app.get(
    "/requests/prioritized",
    response_model=List[schemas.PrioritizedRequestResponse],
    tags=["İhbar Yönetimi"],
    summary="Öncelikli İhbarları Listele",
    description="""
Tüm afet ihbarlarını **dinamik öncelik puanına** göre azalan sırada döner.

**Önceliklendirme Formülü:**
`P = S_base + (S_base × λ × t/M) × (1 + C_i)`

- `S_base`: İhtiyaç türüne göre taban puan (arama_kurtarma=100, medikal=95, yangın=90...)
- `t`: İhbarın kaç saat önce oluşturulduğu
- `M`: İhtiyaç türünün maksimum tolerans süresi (yangın=1 saat, gıda=168 saat)
- `λ`: Zaman hassasiyet katsayısı (1.5)
- `C_i`: İhtiyaç türünün sistem ağırlığı

Bekleyen ihbarların puanı zamanla artar — hiçbir ihbar sonsuza kadar beklemez.
""",
)
def get_prioritized_requests(db: Session = Depends(get_db)):
    return _get_prioritized(db)


def _get_prioritized(db: Session):
    all_requests = db.query(models.DisasterRequest).all()
    results = []
    for req in all_requests:
        score = calculate_dynamic_priority(req.need_type, req.created_at)
        results.append({
            "id": req.id,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "need_type": req.need_type,
            "person_count": getattr(req, "person_count", 1),
            "description": getattr(req, "description", None),
            "status": getattr(req, "status", "pending"),
            "created_at": req.created_at,
            "dynamic_priority_score": score,
            "is_verified": req.is_verified,
        })
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    return results


@app.put(
    "/requests/{request_id}/status",
    tags=["İhbar Yönetimi"],
    summary="İhbar Durumunu Güncelle",
    description="""
Belirtilen ihbarın durumunu günceller.

**Geçerli Durumlar:**
- `pending` — Bekliyor (varsayılan)
- `assigned` — Ekip atandı
- `resolved` — Çözüldü

Durum güncellemesi küme istatistiklerine (pending/assigned/resolved sayıları) yansır.
""",
)
def update_request_status(request_id: str, data: schemas.StatusUpdate, db: Session = Depends(get_db)):
    request = db.query(models.DisasterRequest).filter(models.DisasterRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    request.status = data.status
    db.commit()
    db.refresh(request)
    return request


# ── ARAÇ YÖNETİMİ ─────────────────────────────────────────────────────────

@app.post(
    "/arac-ekle",
    tags=["Araç Yönetimi"],
    summary="Yeni Yardım Aracı Ekle",
    description="Sisteme yeni bir yardım aracı kaydeder. Araç tipi, konum ve kapasite bilgileri alınır.",
)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = models.ReliefVehicle(**vehicle.model_dump())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


@app.get(
    "/araclar",
    tags=["Araç Yönetimi"],
    summary="Tüm Araçları Listele",
    description="Sistemdeki tüm yardım araçlarını ve stok bilgilerini (çadır, gıda, su, tıbbi malzeme, battaniye) döner.",
)
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(models.ReliefVehicle).all()


@app.get(
    "/yakin-araclar",
    tags=["Araç Yönetimi"],
    summary="Yakındaki Araçları Getir (Öklid)",
    description="""
Verilen koordinata yakın araçları döner.

Mesafe hesabı Öklid formülüyle yapılır (yaklaşık 10 km eşiği).
Daha hassas coğrafi sorgular için `/yakin-araclar-postgis` kullanın.
""",
)
def get_nearby_vehicles(lat: float, lon: float, db: Session = Depends(get_db)):
    vehicles = db.query(models.ReliefVehicle).all()
    return [v for v in vehicles if sqrt((v.latitude - lat)**2 + (v.longitude - lon)**2) < 0.1]


@app.get(
    "/yakin-araclar-sql",
    tags=["Araç Yönetimi"],
    summary="Yakındaki Araçları Getir (SQL)",
    description="Tüm araçları SQL sorgusuyla döner. Filtreleme yapılmaz, tüm araçlar listelenir.",
)
def get_nearby_sql(lat: float, lon: float, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM relief_vehicles"))
    return [dict(row._mapping) for row in result]


@app.get(
    "/yakin-araclar-postgis",
    tags=["Araç Yönetimi"],
    summary="Yakındaki Araçları Getir (PostGIS)",
    description="""
PostGIS `ST_DWithin` fonksiyonuyla verilen koordinata 5 km yarıçap içindeki araçları döner.

Küresel mesafe hesabı yapıldığı için Öklid yöntemine göre çok daha doğrudur.
Araç tablosunda `location` geometry kolonu gerektirir.
""",
)
def get_nearby_postgis(lat: float, lon: float, db: Session = Depends(get_db)):
    query = text("""
        SELECT * FROM relief_vehicles
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 5000)
    """)
    result = db.execute(query, {"lat": lat, "lon": lon})
    return [dict(row._mapping) for row in result]


@app.put(
    "/arac-guncelle/{vehicle_id}",
    tags=["Araç Yönetimi"],
    summary="Araç Stok Bilgilerini Güncelle",
    description="Belirtilen aracın stok bilgilerini (çadır, gıda, su, tıbbi malzeme, battaniye sayıları) günceller.",
)
def update_vehicle(vehicle_id: str, data: schemas.VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for field, value in data.model_dump().items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.post(
    "/assign-vehicle",
    tags=["Araç Yönetimi"],
    summary="Araca Küme Ata",
    description="""
Bir yardım aracını belirtilen ihbar kümesine atar ve araç stoğunu günceller.

**İşlem Adımları:**
1. Araç ve küme veritabanında aranır.
2. Aracın çadır stoğu, kümedeki etkilenen kişi sayısıyla karşılaştırılır.
3. Stok yeterliyse çadır sayısı düşülür ve işlem kaydedilir.
4. Saha şoförüne konsol üzerinden bildirim simülasyonu gönderilir (Görev 4.2).

Stok yetersizse HTTP 400 döner.
""",
)
def assign_vehicle(data: schemas.AssignVehicleRequest, db: Session = Depends(get_db)):
    vehicle = db.query(models.ReliefVehicle).filter(models.ReliefVehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    cluster = db.query(models.Cluster).filter(models.Cluster.id == data.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    needed = cluster.total_persons_affected
    if vehicle.tent_count < needed:
        raise HTTPException(status_code=400, detail="Not enough tent stock")
    vehicle.tent_count -= needed
    db.commit()
    db.refresh(vehicle)
    send_assignment_notification(
        cluster_name=cluster.cluster_name,
        center_lat=cluster.center_latitude,
        center_lon=cluster.center_longitude,
        total_persons=needed,
        need_type=cluster.need_type,
    )
    return {"message": "Vehicle assigned and stock updated", "remaining_tents": vehicle.tent_count}


# ── DEPREM VERİLERİ ────────────────────────────────────────────────────────

@app.get(
    "/buyuk-depremler",
    tags=["Deprem Verileri"],
    summary="Son 3 Ayın Büyük Depremlerini Getir",
    description="""
USGS (ABD Jeoloji Kurumu) API'sinden son 3 ayda Türkiye'de gerçekleşen
**5.0 ve üzeri büyüklükteki** depremleri çeker.

**Kapsama Alanı:** 36–42° Kuzey enlemi, 26–45° Doğu boylamı (Türkiye sınırları)

Sonuçlar en yeniden eskiye sıralı döner. Her deprem için konum, büyüklük ve tarih bilgisi içerir.

> Kandilli API'si tarih filtresi desteklemediğinden bu endpoint USGS kullanır.
""",
)
def get_major_earthquakes():
    return get_major_earthquakes_last_3_months()


# ── OPERASYON ─────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Gerçek zamanlı WebSocket bağlantısı.
    Bağlanan istemciler yeni ihbar, küme güncellemesi ve operasyon başlatma
    gibi olayları anlık olarak alır.
    """
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class SuruBaslatSchema(BaseModel):
    sektor_id: str
    aksiyon: str


@app.post(
    "/api/operasyon/suru-baslat",
    tags=["Operasyon"],
    summary="Otonom Sürü Operasyonu Başlat",
    description="""
Belirtilen sektörde otonom sürü operasyonu başlatır.

WebSocket üzerinden bağlı tüm istemcilere `SWARM_STARTED` eventi iletilir.
Saha ekipleri ve drone birimleri bu event'i dinleyerek harekete geçer.

**Parametreler:**
- `sektor_id`: Operasyonun başlatılacağı sektör kodu (örn: "A1", "B3")
- `aksiyon`: Yapılacak işlem (örn: "tarama", "tahliye", "malzeme_dagitimi")
""",
)
async def start_swarm_operation(data: SuruBaslatSchema):
    print(f"OPERASYON: {data.sektor_id} bölgesinde {data.aksiyon} tetiklendi!")
    await manager.broadcast({"event": "SWARM_STARTED", "sector": data.sektor_id, "action": data.aksiyon})
    return {"status": "started", "detail": f"{data.sektor_id} için operasyon başladı."}
