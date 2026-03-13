# Afet Koordinasyon API (Backend)

Bu proje, afet yönetimi ve koordinasyonu için geliştirilmiş, **FastAPI** ve **PostgreSQL (Supabase)** tabanlı bir REST API'dir.

## Kurulum ve Çalıştırma

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Ana dizinde `.env` dosyası oluşturup veritabanı url'sini ekleyin:
   ```env
   DATABASE_URL="postgresql://kullanici:sifre@host:port/veritabani"
   ```
3. API sunucusunu başlatın:
   ```bash
   uvicorn main:app --reload
   ```
   API dokümantasyonuna [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) adresinden erişebilirsiniz.

## API Endpoint'leri

### `GET /`
Ana sayfa kontrolü.
| Alan | Değer |
|------|-------|
| **Yanıt** | `{"message": "Afet Koordinasyon API çalışıyor"}` |

---

### `POST /talep-gonder`
Yeni bir afetzede talebi oluşturur ve veritabanına kaydeder.

**Gönderilecek JSON:**
```json
{
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal"
}
```

**Yanıt (201):**
```json
{
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal",
  "id": "uuid-formatinda-id",
  "created_at": "2026-03-13T14:00:00.000000"
}
```

---

### `GET /talepler/oncelikli`
Veritabanındaki tüm talepleri **öncelik puanına göre en acilden en aza** sıralayarak döndürür. Frontend bu endpoint'i çekerek listeyi gösterecek.

**Yanıt (200):**
```json
[
  {
    "latitude": 41.01,
    "longitude": 29.02,
    "need_type": "arama_kurtarma",
    "id": "uuid-formatinda-id",
    "created_at": "2026-03-13T14:00:00.000000",
    "oncelik_puani": 100
  }
]
```

**Öncelik Puan Tablosu:**

| need_type | Puan | Açıklama |
|-----------|------|----------|
| arama_kurtarma | 100 | Enkaz altında kalan kişiler |
| enkaz | 95 | Bina çökmesi, yapısal hasar |
| medikal | 90 | Kanamalı yaralı, tıbbi müdahale |
| yangin | 85 | Aktif yangın tehlikesi |
| is_makinesi | 75 | İş makinesi talebi |
| barinma | 60 | Çadır / hipotermi riski |
| su | 50 | Temiz su ihtiyacı |
| gida | 40 | Gıda / yemek ihtiyacı |
| ulasim | 30 | Ulaşım desteği |

## Dosya Yapısı

| Dosya | Görevi |
|-------|--------|
| `main.py` | FastAPI uygulaması ve endpoint'ler |
| `database.py` | PostgreSQL veritabanı bağlantısı |
| `models.py` | SQLAlchemy tablo modelleri (`afetzede_talepleri`) |
| `schemas.py` | Pydantic veri doğrulama şemaları |
| `priority_engine.py` | İhtiyaç türüne göre öncelik puanlama motoru |
| `mock_data_generator.py` | İstanbul için sahte veri üreten bot (`python mock_data_generator.py`) |
| `live_earthquake_data.py` | Kandilli API'sinden son depremleri çeken script |