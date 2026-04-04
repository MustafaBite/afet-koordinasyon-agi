# Afet Koordinasyon API - Backend

FastAPI + PostgreSQL tabanlı afet yönetim sistemi backend'i. AI destekli araç önerisi, dinamik önceliklendirme ve coğrafi kümeleme özellikleri sunar.

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarla
`.env` dosyası oluşturun:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/afet_koordinasyon
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Veritabanını Hazırla
```bash
# PostgreSQL'de veritabanı oluştur
createdb afet_koordinasyon

# PostGIS extension'ı ekle
psql -d afet_koordinasyon -c "CREATE EXTENSION postgis;"

# Migration'ları çalıştır
psql -U user -d afet_koordinasyon -f migrations/add_base_speed_to_vehicles.sql
psql -U user -d afet_koordinasyon -f migrations/add_vehicle_recommendation_fields.sql
```

### 4. Sunucuyu Başlat
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://localhost:8000
- Swagger Dokümantasyon: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📋 Özellikler

### Temel Özellikler
- ✅ **JWT Authentication** - Token tabanlı güvenli kimlik doğrulama
- ✅ **Role-based Access Control** - Rol bazlı yetkilendirme sistemi
- ✅ **DBSCAN Clustering** - Coğrafi kümeleme algoritması
- ✅ **Dynamic Priority Scoring** - Dinamik öncelik hesaplama
- ✅ **Real-time Earthquake Verification** - Canlı deprem doğrulama
- ✅ **Reverse Geocoding** - Koordinattan adres bulma
- ✅ **WebSocket Support** - Gerçek zamanlı güncellemeler

### Gelişmiş Özellikler
- ✅ **Otonom Araç Önerisi Sistemi** - AI destekli MCDM algoritması
- ✅ **Tahmini Varış Süresi (ETA)** - Gerçek zamanlı hesaplama

## 🧪 Testler

```bash
# Tüm testleri çalıştır
python -m pytest tests/

# Kimlik doğrulama testleri
python tests/test_auth.py

# Araç önerisi ve ETA testleri
python tests/test_vehicle_recommendation.py

# Entegrasyon testleri
python tests/test_integration.py
```

## 📚 API Endpoint'leri

### Kimlik Doğrulama
```bash
POST   /auth/register          # Kullanıcı kaydı
POST   /auth/login             # Kullanıcı girişi
GET    /auth/me                # Mevcut kullanıcı bilgisi
PUT    /auth/me                # Profil güncelleme
```

### Afet İhbarları
```bash
POST   /requests               # Yeni ihbar oluştur
GET    /requests/prioritized   # Öncelikli ihbarları listele
PUT    /requests/{id}/status   # İhbar durumunu güncelle
```

### Kümeler (Task Packages)
```bash
POST   /requests/task-packages/generate                    # Kümeleme çalıştır
GET    /requests/task-packages                             # Kümeleri listele
GET    /requests/task-packages/{id}                        # Küme detayı
GET    /requests/task-packages/{id}/recommend-vehicles     # Araç önerisi
POST   /requests/task-packages/{id}/assign-vehicle         # Araç atama ve ETA
```

### Araçlar
```bash
POST   /api/vehicles           # Yeni araç ekle
GET    /api/vehicles           # Araçları listele
GET    /api/vehicles/{id}      # Araç detayı
PUT    /api/vehicles/{id}      # Araç güncelle
DELETE /api/vehicles/{id}      # Araç sil
```

## 🎯 Otonom Araç Önerisi ve ETA Detayları

### Araç Önerisi Sistemi
Bir küme için en uygun aracı AI ile önerir.

**Endpoint:**
```bash
GET /requests/task-packages/{cluster_id}/recommend-vehicles?top_n=3
```

**Algoritma:**
- Aciliyet: %40
- Mesafe/ETA: %27
- Stok Yeterliliği: %18
- Araç Hızı: %15

**Örnek Yanıt:**
```json
{
  "vehicle_id": "uuid",
  "vehicle_type": "Kamyon",
  "capacity": "10 Ton",
  "score": 87.5,
  "details": {
    "distance_km": 5.2,
    "eta_minutes": 8,
    "available_stock": 100,
    "required_quantity": 50
  },
  "recommendation_text": "Bu kümenin 50 çadır ihtiyacı var..."
}
```

### ETA (Tahmini Varış Süresi)
Araç atandığında otomatik ETA hesaplanır.

**Endpoint:**
```bash
POST /requests/task-packages/{cluster_id}/assign-vehicle?vehicle_id={vehicle_id}
```

**Formül:**
```
ETA (dakika) = (Mesafe × 1.2) / Araç Hızı × 60
```

**Örnek Yanıt:**
```json
{
  "message": "Araç başarıyla atandı",
  "distance_km": 5.2,
  "eta_minutes": 8,
  "remaining_stock": 50,
  "cluster_status": "resolved"
}
```

## 📁 Proje Yapısı (Modüler Mimari)

```
backend/
├── core/                                 # Merkezi Bağımlılıklar
│   ├── __init__.py
│   └── dependencies.py                   # Database session yönetimi
│
├── utils/                                # Yardımcı Fonksiyonlar
│   ├── __init__.py
│   ├── geo.py                           # Coğrafi hesaplamalar (Haversine, vb.)
│   └── websocket.py                     # WebSocket bağlantı yönetimi
│
├── routers/                              # API Endpoint'leri
│   ├── __init__.py
│   ├── auth.py                           # Kimlik doğrulama
│   ├── clusters.py                       # Kümeleme ve araç önerisi
│   ├── requests.py                       # İhbar yönetimi
│   └── vehicles.py                       # Araç CRUD
│
├── services/                             # İş Mantığı Servisleri
│   ├── __init__.py
│   ├── priority.py                      # Dinamik önceliklendirme
│   ├── clustering.py                    # DBSCAN kümeleme algoritması
│   └── vehicle_recommendation.py        # Araç önerisi ve ETA hesaplama
│
├── scripts/                              # Yardımcı Scriptler
│   └── generate_mock_data.py            # Test verisi oluşturucu
│
├── tests/                                # Test Dosyaları
│   ├── __init__.py
│   ├── test_auth.py                      # Auth testleri
│   ├── test_vehicle_recommendation.py    # Araç önerisi testleri
│   └── test_integration.py               # Entegrasyon testleri
│
├── docs/                                 # Dokümantasyon
│   ├── API.md                           # API referansı
│   └── DATABASE_SCHEMA.md               # Veritabanı şeması
│
├── migrations/                           # SQL Migration'ları
│   ├── add_base_speed_to_vehicles.sql
│   └── add_vehicle_recommendation_fields.sql
│
├── models.py                             # SQLAlchemy Modelleri
├── schemas.py                            # Pydantic Şemaları
├── database.py                           # Veritabanı Bağlantısı
│
├── geocoder.py                           # Reverse Geocoding
├── live_earthquake_data.py               # Canlı Deprem Verileri
│
├── main.py                               # FastAPI Uygulaması
├── requirements.txt                      # Python Bağımlılıkları
└── README.md                            
```

### Modüler Yapı Avantajları
- ✅ **Tek Sorumluluk İlkesi**: Her modül tek bir işten sorumlu
- ✅ **Kod Tekrarı Yok**: Ortak fonksiyonlar merkezi konumda
- ✅ **Kolay Test**: Her modül bağımsız test edilebilir
- ✅ **Bakım Kolaylığı**: Değişiklikler tek yerden yapılır
- ✅ **Ölçeklenebilir**: Yeni modüller kolayca eklenebilir

## 🔧 Algoritmalar

### 1. Dinamik Önceliklendirme
```python
def calculate_dynamic_priority(need_type, created_at):
    base_score = NEED_TYPE_SCORES.get(need_type, 50)
    time_factor = calculate_time_factor(created_at)
    return base_score * time_factor
```

**İhtiyaç Tipi Skorları:**
- Arama Kurtarma: 100
- Medikal: 90
- Yangın: 85
- Enkaz: 80
- Su: 70
- Barınma: 60
- Gıda: 50

### 2. DBSCAN Kümeleme
```python
clustering = DBSCAN(
    eps=0.5,              # 500 metre yarıçap
    min_samples=2,        # Minimum 2 ihbar
    metric='haversine'    # Küresel mesafe
)
```

### 3. Araç Önerisi (MCDM)
```python
total_score = (
    urgency_score × 0.40 +
    distance_score × 0.27 +
    stock_score × 0.18 +
    speed_score × 0.15
)
```

### 4. ETA Hesaplama
```python
def calculate_eta(distance_km, vehicle_speed, priority_score):
    speed = vehicle_speed
    if priority_score >= 75:
        speed *= 1.1  # Kritik durumlarda +10% hız
    
    adjusted_distance = distance_km * 1.2  # Afet düzeltmesi
    eta_hours = adjusted_distance / speed
    return int(eta_hours * 60)  # Dakikaya çevir
```

## 🗄️ Veritabanı Modelleri

### Ana Tablolar
- `app_users` - Kullanıcılar
- `disaster_requests` - Afet ihbarları
- `clusters` - Kümelenmiş görev paketleri
- `relief_vehicles` - Yardım araçları
- `teams` - Ekipler

Detaylı şema için: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

## 🔐 Güvenlik

### JWT Token
- Geçerlilik süresi: 7 gün
- Algorithm: HS256
- Secret key: Ortam değişkeninden

### Şifre Hashleme
- Bcrypt algoritması
- Salt rounds: 12

### CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da değiştir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Mock Veri Oluşturma

```bash
# Rastgele 500 ihbar
python mock_data_generator.py

# Kümelenmiş test verisi
python mock_data_generator.py --clustered

# Belirli sayıda ihbar
python mock_data_generator.py --count 100
```

## 🚀 Production Deployment

### Gunicorn ile Çalıştırma
```bash
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Ortam Değişkenleri (Production)
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=strong-random-key-here
ALLOWED_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
```

## 📖 Dokümantasyon

- [API Dokümantasyonu](docs/API.md) - Tüm endpoint'ler ve örnekler
- [Veritabanı Şeması](docs/DATABASE_SCHEMA.md) - ER diagram ve ilişkiler

## 📂 Modül Açıklamaları

### core/
Merkezi bağımlılıklar ve yapılandırma dosyaları.
- `dependencies.py`: Database session yönetimi (`get_db()`)

### utils/
Yardımcı fonksiyonlar ve araçlar.
- `geo.py`: Coğrafi hesaplamalar (Haversine formülü, deprem yakınlık kontrolü)
- `websocket.py`: WebSocket bağlantı yönetimi (`ConnectionManager`)

### routers/
API endpoint'lerini içeren router modülleri.
- `auth.py`: Kimlik doğrulama (register, login, profile)
- `clusters.py`: Kümeleme ve araç önerisi
- `requests.py`: İhbar yönetimi
- `vehicles.py`: Araç CRUD işlemleri

### services/
İş mantığı katmanı (gelecek genişlemeler için hazır).

### tests/
Otomatik test dosyaları.
- `test_auth.py`: Kimlik doğrulama testleri
- `test_vehicle_recommendation.py`: Araç önerisi ve ETA testleri
- `test_integration.py`: Entegrasyon testleri

## 🤝 Katkıda Bulunma

1. Issue açın veya mevcut bir issue'yu seçin
2. Feature branch oluşturun
3. Testlerinizi yazın
4. Pull request açın

## 📝 Notlar

- Test verileri için `mock_data_generator.py` kullanın
- Migration'ları sırayla çalıştırın
- Production'da `SECRET_KEY` mutlaka değiştirin
- CORS ayarlarını production için güncelleyin
