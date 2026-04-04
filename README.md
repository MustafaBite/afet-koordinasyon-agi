# Afet Koordinasyon Ağı
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Gerçek zamanlı afet yönetimi ve koordinasyon sistemi. AI destekli araç önerisi, dinamik önceliklendirme ve kümeleme algoritmaları ile afet durumlarında hızlı ve etkili müdahale sağlar.

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- PostGIS extension

### Backend Kurulumu
```bash
cd backend
pip install -r requirements.txt

# .env dosyası oluştur
echo "DATABASE_URL=postgresql://user:password@localhost/afet_koordinasyon" > .env
echo "SECRET_KEY=your-secret-key-change-in-production" >> .env

# Migration'ları çalıştır
psql -U user -d afet_koordinasyon -f migrations/add_base_speed_to_vehicles.sql

# Sunucuyu başlat
uvicorn main:app --reload
```

API: http://localhost:8000  
Swagger Dokümantasyon: http://localhost:8000/docs

### Frontend Kurulumu
```bash
cd kriz-paneli
npm install
npm run dev
```

Frontend: http://localhost:5173

## 📋 Özellikler

### Temel Özellikler
- **Kullanıcı Yönetimi**: JWT tabanlı kimlik doğrulama ve rol bazlı yetkilendirme
  - Roller: Vatandaş, Gönüllü, Koordinatör, Yönetici
  - Profil yönetimi ve güncelleme
  - Güvenli şifre hashleme (bcrypt)

- **Afet İhbar Sistemi**: Gerçek zamanlı ihbar oluşturma ve takip
  - Coğrafi konum bazlı ihbarlar
  - Otomatik deprem doğrulama (AFAD/Kandilli verileri)
  - İhtiyaç tipi kategorilendirme

- **Dinamik Önceliklendirme**: Zaman ve aciliyet bazlı skorlama
  - Otomatik öncelik hesaplama
  - Kritik/Yüksek/Orta/Düşük seviyelendirme
  - Zaman faktörü ile dinamik güncelleme

- **DBSCAN Kümeleme**: Coğrafi yakınlık bazlı görev paketleri
  - Otomatik küme oluşturma
  - Adres bilgisi zenginleştirme (reverse geocoding)
  - Küme durumu takibi

- **Takım Yönetimi**: Ekip oluşturma ve görevlendirme
  - Kapasite yönetimi
  - Konum bazlı atama
  - Performans takibi

### Gelişmiş Özellikler

#### 🚗 Otonom Araç Önerisi Sistemi
AI destekli çok kriterli karar verme (MCDM) algoritması ile en uygun aracı otomatik önerir.

**Algoritma Kriterleri:**
- Aciliyet: %40 (Kümenin öncelik skoru)
- Mesafe: %27 (ETA hesaplaması)
- Stok Yeterliliği: %18 (Gerekli malzeme kontrolü)
- Araç Hızı: %15 (Hızlı müdahale)

**Örnek Kullanım:**
```
Küme: 20 kişi, barınma ihtiyacı
Sistem Önerisi: "Bu kümenin 5 çadır ihtiyacı var. En yakın ve stokta 
en az 5 çadır olan araç: Kamyon (10 Ton). Mesafe: 5.2 km, 
Tahmini Varış: 8 dakika. Skor: 87.5/100"
```

#### ⏱️ Tahmini Varış Süresi (ETA) Hesaplama
Haversine formülü ile hassas mesafe hesaplama ve gerçekçi varış süresi tahmini.

**Hesaplama Yöntemi:**
```
ETA (dakika) = (Mesafe × Afet Düzeltme Katsayısı) / Araç Hızı × 60
```

**Özellikler:**
- Haversine formülü ile kuş uçuşu mesafe
- Afet koşulları düzeltmesi (×1.2 katsayı)
- Kritik durumlarda hız optimizasyonu (%10 artış)
- Araç tipine göre hız ayarlaması

## 🧪 Testler

```bash
cd backend

# Kimlik doğrulama testleri
python tests/test_auth.py

# Araç önerisi ve ETA testleri
python tests/test_vehicle_recommendation.py

# Entegrasyon testleri
python tests/test_integration.py
```

## 📚 Dokümantasyon

- [Backend README](backend/README.md) - Backend detaylı kurulum ve kullanım
- [API Dokümantasyonu](backend/docs/API.md) - Tüm endpoint'ler ve örnekler
- [Veritabanı Şeması](backend/docs/DATABASE_SCHEMA.md) - ER diagram ve ilişkiler

## 🎯 API Kullanım Örnekleri

### Otonom Araç Önerisi
```bash
GET /requests/task-packages/{cluster_id}/recommend-vehicles?top_n=3
```

**Yanıt:**
```json
{
  "vehicle_type": "Kamyon",
  "capacity": "10 Ton",
  "score": 87.5,
  "details": {
    "distance_km": 5.2,
    "eta_minutes": 8,
    "available_stock": 100,
    "required_quantity": 50,
    "stock_score": 100.0,
    "distance_score": 85.3,
    "speed_score": 75.0,
    "urgency_score": 82.5
  },
  "recommendation_text": "Bu kümenin 50 çadır ihtiyacı var. En yakın araç: Kamyon..."
}
```

### Araç Atama ve ETA Hesaplama
```bash
POST /requests/task-packages/{cluster_id}/assign-vehicle?vehicle_id={vehicle_id}
```

**Yanıt:**
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
afet-koordinasyon-agi/
├── backend/                          # FastAPI Backend
│   ├── core/                         # Merkezi Bağımlılıklar
│   │   ├── __init__.py
│   │   └── dependencies.py           # Database session yönetimi
│   │
│   ├── utils/                        # Yardımcı Fonksiyonlar
│   │   ├── __init__.py
│   │   ├── geo.py                   # Coğrafi hesaplamalar
│   │   └── websocket.py             # WebSocket yönetimi
│   │
│   ├── services/                     # İş Mantığı Servisleri
│   │   ├── __init__.py
│   │   ├── priority.py              # Dinamik önceliklendirme
│   │   ├── clustering.py            # DBSCAN kümeleme
│   │   └── vehicle_recommendation.py # Araç önerisi ve ETA
│   │
│   ├── routers/                      # API Endpoint'leri
│   │   ├── auth.py                   # Kimlik doğrulama
│   │   ├── clusters.py               # Kümeleme ve araç önerisi
│   │   ├── requests.py               # İhbar yönetimi
│   │   └── vehicles.py               # Araç CRUD
│   │
│   ├── scripts/                      # Yardımcı Scriptler
│   │   └── generate_mock_data.py    # Test verisi oluşturucu
│   │
│   ├── tests/                        # Test dosyaları
│   │   ├── test_auth.py
│   │   ├── test_vehicle_recommendation.py
│   │   └── test_integration.py
│   │
│   ├── docs/                         # Dokümantasyon
│   │   ├── API.md
│   │   └── DATABASE_SCHEMA.md
│   │
│   ├── migrations/                   # SQL migration'ları
│   ├── models.py                     # Veritabanı modelleri
│   ├── schemas.py                    # Pydantic şemaları
│   ├── geocoder.py                   # Reverse geocoding
│   ├── live_earthquake_data.py       # Deprem verileri
│   └── main.py                       # FastAPI uygulaması
│
├── kriz-paneli/                      # React Frontend
│   └── src/
│       ├── components/               # UI bileşenleri
│       │   ├── common/              # Ortak bileşenler
│       │   ├── Dashboard.jsx
│       │   ├── Header.jsx
│       │   └── Sidebar.jsx
│       ├── pages/                    # Sayfalar
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   └── Profile.jsx
│       ├── services/                 # API servisleri
│       │   └── authService.js
│       └── utils/                    # Yardımcı fonksiyonlar
│           └── validation.js
│
└── .env                              # Ortam değişkenleri
```

## 🔐 Güvenlik

- JWT token tabanlı kimlik doğrulama (7 gün geçerlilik)
- Bcrypt ile şifre hashleme
- CORS middleware
- SQL injection koruması (SQLAlchemy ORM)
- Input validasyonu (Pydantic)
- Role-based access control (RBAC)

## 🛠️ Teknolojiler

### Backend
- FastAPI - Modern, hızlı web framework
- PostgreSQL + PostGIS - Coğrafi veritabanı
- SQLAlchemy - ORM
- Pydantic - Veri validasyonu
- JWT - Token tabanlı auth
- Bcrypt - Şifre hashleme
- Scikit-learn - DBSCAN kümeleme
- Geopy - Geocoding

### Frontend
- React 18 - UI framework
- Vite - Build tool
- TailwindCSS - Styling
- Leaflet - Harita görünümü

## 🌍 Ortam Değişkenleri

`.env` dosyası oluşturun:
```env
# Veritabanı
DATABASE_URL=postgresql://user:password@localhost:5432/afet_koordinasyon

# Güvenlik
SECRET_KEY=your-secret-key-change-in-production

# CORS (Production için)
ALLOWED_ORIGINS=https://yourdomain.com
```

## 📊 Algoritmalar

### 1. Dinamik Önceliklendirme
```python
score = base_score × time_factor × verification_bonus
```
- Base score: İhtiyaç tipine göre (0-100)
- Time factor: Zaman geçtikçe artar
- Verification bonus: Doğrulanmış ihbarlar için +20%

### 2. DBSCAN Kümeleme
- Epsilon: 0.5 km (coğrafi yakınlık)
- Min samples: 2 (minimum ihbar sayısı)
- Metric: Haversine (küresel mesafe)

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
eta_minutes = (distance_km × 1.2) / vehicle_speed × 60
```
- Afet düzeltme katsayısı: 1.2
- Kritik durumlarda: +10% hız

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'feat: Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👥 Ekip

- **Frontend Geliştirici & Proje Yöneticisi:** [@zehradagasann](https://github.com/zehradagasann)
- **Backend Geliştiriciler:**
  - [@BilalAbic](https://github.com/BilalAbic)
  - [@Perihanceliko](https://github.com/Perihanceliko)
  - [@MustafaBite](https://github.com/MustafaBite)

## 📞 İletişim

Proje ile ilgili sorularınız için issue açabilirsiniz.
