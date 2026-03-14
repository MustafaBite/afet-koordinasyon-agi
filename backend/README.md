# Afet Koordinasyon API (Backend)

Bu proje, afet yönetimi ve koordinasyonu için geliştirilmiş, **FastAPI** ve **PostgreSQL (Supabase)** tabanlı bir REST API'dir.

## Kurulum ve Çalıştırma

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Ana dizinde `.env` dosyası oluşturup veritabanı URL'sini ekleyin:
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
Sunucu durumunu kontrol eder.

**Yanıt:** `{"message": "Afet Koordinasyon API çalışıyor"}`

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

**Yanıt (200):**
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
Tüm talepleri **dinamik öncelik puanına göre en acilden en aza** sıralayarak döndürür. Puan, taban değer + bekleme süresine dayalı Zaman Sönümleme (Time Decay / DPS) formülüyle hesaplanır.

**Yanıt (200):**
```json
[
  {
    "latitude": 41.01,
    "longitude": 29.02,
    "need_type": "arama_kurtarma",
    "id": "uuid-formatinda-id",
    "created_at": "2026-03-12T08:00:00.000000",
    "dynamic_priority_score": 85.5
  }
]
```

| Alan | Açıklama |
|------|----------|
| **`dynamic_priority_score`** | **Sıralamanın yapıldığı asıl değer.** 0-100% aralığında normalize edilmiş güncel aciliyet yüzdesi. |

---

## Öncelik Puanlama Sistemi

### Taban Puanları ve Ağırlık Katsayıları (ÇKKV / AHP)

| need_type | Taban Puan | Ağırlık (C_i) | Maks. Tolerans | Açıklama |
|-----------|-----------|---------------|----------------|----------|
| arama_kurtarma | 100 | 0.25 | 6 saat | Enkaz altı, crush sendromu |
| medikal | 95 | 0.20 | 2 saat | Ağır travma, altın saat |
| yangin | 90 | 0.15 | 1 saat | Hızlı yayılma, sekonder felaket |
| enkaz | 80 | 0.12 | 12 saat | Yapısal hasar, potansiyel kurtarma |
| su | 60 | 0.09 | 72 saat | Dehidrasyon sınırı (~3 gün) |
| barinma | 50 | 0.07 | 48 saat | Hipotermi/hipertermi riski |
| gida | 40 | 0.06 | 168 saat | Açlık toleransı (~7 gün) |
| is_makinesi | 35 | 0.04 | 24 saat | Lojistik destek unsuru |
| ulasim | 25 | 0.02 | 24 saat | Tahliye ve nakliye |

### Zaman Sönümleme Formülü (DPS)

```
P_dynamic(t) = S_base + (S_base × λ × (t / M)) × (1 + C_i)
```

- **λ (lambda):** Zaman duyarlılık çarpanı (varsayılan: 1.5)
- **t:** Bekleme süresi (saat)
- **M:** Kategorinin maks. tolerans süresi

> **Not:** Dinamik önceliklendirme motorunun temelini oluşturan algoritmik karar destek sistemi (ÇKKV/AHP, ve Zaman Sönümleme/DPS formülleri) **Google Gemini** kullanılarak araştırılmış ve tasarlanmıştır. Detaylı araştırma dokümanına [buradan](https://docs.google.com/document/d/1BdAMHpEGyv_WbslJ7ysQ6LxKDYFSQd_VBGNX3WtlsBE/edit?usp=sharing) ulaşabilirsiniz.

## Dosya Yapısı

| Dosya | Görevi |
|-------|--------|
| `main.py` | FastAPI uygulaması ve endpoint'ler |
| `database.py` | PostgreSQL veritabanı bağlantısı |
| `models.py` | SQLAlchemy tablo modelleri (`disaster_requests`) |
| `schemas.py` | Pydantic veri doğrulama şemaları |
| `priority_engine.py` | Dinamik önceliklendirme motoru |
| `mock_data_generator.py` | İstanbul için sahte veri üreten bot (`python mock_data_generator.py`) |
| `live_earthquake_data.py` | Kandilli API'sinden son depremleri çeken script |