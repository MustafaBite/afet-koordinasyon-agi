# Afet Koordinasyon API (Backend)

FastAPI + PostgreSQL tabanlı REST API.

---

## Kurulum

1. Bağımlılıkları yükle:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` dosyası oluştur:
   ```env
   DATABASE_URL="postgresql://kullanici:sifre@host:port/veritabani"
   SECRET_KEY="your-secret-key-change-in-production"
   ```

3. Veritabanı tablolarını oluştur:
   > **Not:** Takım arkadaşlarımın bu adımı yapmasına gerek yok. Sadece veritabanı sıfırlandıysa yaparsınız.
   ```bash
   python -c "from database import engine; from models import Base; Base.metadata.create_all(engine)"
   ```

4. Sunucuyu başlat:
   ```bash
   uvicorn main:app --reload
   ```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Dokümantasyon

- **[API Dokümantasyonu](API_DOCUMENTATION.md)** - Tüm endpoint'ler ve kullanım örnekleri
- **[Veritabanı Şeması](DATABASE_SCHEMA.md)** - ER diagram ve ilişkiler

---

## Dosya Yapısı

```
backend/
├── routers/
│   ├── auth.py              # Authentication endpoints
│   ├── requests.py          # Disaster request endpoints
│   └── clusters.py          # Cluster endpoints
├── models.py                # Database models
├── schemas.py               # Pydantic schemas
├── main.py                  # FastAPI app
├── database.py              # DB connection
├── clustering_engine.py     # DBSCAN algorithm
├── priority_engine.py       # Priority scoring
├── geocoder.py              # Reverse geocoding
├── test_auth.py             # API tests
└── test_integration.py      # Integration tests
```

---

## Testler

```bash
# API testleri
python test_auth.py

# Entegrasyon testleri
python test_integration.py
```

---

## Özellikler

- ✅ JWT Authentication
- ✅ Role-based access control
- ✅ DBSCAN spatial clustering
- ✅ Dynamic priority scoring
- ✅ Real-time earthquake verification
- ✅ Reverse geocoding
- ✅ WebSocket support

---

## Mock Veri

```bash
# Rastgele 500 kayıt
python mock_data_generator.py

# Kümelenmiş test verisi
python mock_data_generator.py --clustered
```
