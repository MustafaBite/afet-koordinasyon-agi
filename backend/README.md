# Afet Koordinasyon API (Backend)

Afet yönetimi ve koordinasyonu için geliştirilmiş **FastAPI** + **PostgreSQL** tabanlı REST API.

---

## Kurulum

1. Bağımlılıkları yükle:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` dosyası oluştur:
   ```env
   DATABASE_URL="postgresql://kullanici:sifre@host:port/veritabani"
   ```

3. Veritabanı tablolarını oluştur:
   ```bash
   python -c "from database import engine; from models import Base; Base.metadata.create_all(engine)"
   ```

4. (Opsiyonel) Mock veri yükle:
   ```bash
   python mock_data_generator.py --clustered
   ```

5. Sunucuyu başlat:
   ```bash
   uvicorn main:app --reload
   ```

Swagger dokümantasyonu: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Dosya Yapısı

```
backend/
├── main.py                  # Uygulama başlangıcı, middleware, router kayıtları
├── database.py              # SQLAlchemy bağlantısı
├── models.py                # ORM modelleri (DisasterRequest, Cluster)
├── schemas.py               # Pydantic şemaları (request/response)
├── priority_engine.py       # Dinamik önceliklendirme motoru (DPS)
├── clustering_engine.py     # DBSCAN mekansal kümeleme motoru
├── geocoder.py              # Ters geocoding (Nominatim / OpenStreetMap)
├── mock_data_generator.py   # Test verisi üretici
└── routers/
    ├── requests.py          # /requests endpoint'leri
    └── clusters.py          # /requests/task-packages endpoint'leri
```

---

## Veri Modelleri

### `DisasterRequest` Tablosu

| Alan | Tip | Açıklama |
|------|-----|----------|
| `id` | UUID | Birincil anahtar |
| `latitude` | Float | Enlem |
| `longitude` | Float | Boylam |
| `need_type` | String | İhtiyaç tipi |
| `person_count` | Integer | Etkilenen kişi sayısı (varsayılan: 1) |
| `description` | String | Opsiyonel açıklama notu |
| `status` | Enum | `pending` / `assigned` / `resolved` |
| `created_at` | DateTime | Oluşturulma zamanı (UTC) |

### `Cluster` Tablosu

| Alan | Tip | Açıklama |
|------|-----|----------|
| `id` | UUID | Birincil anahtar (kalıcı küme kimliği) |
| `need_type` | String | İhtiyaç tipi |
| `cluster_name` | String | Otomatik üretilen küme adı |
| `center_latitude` | Float | Küme merkez enlem |
| `center_longitude` | Float | Küme merkez boylam |
| `district` | String | İlçe |
| `neighborhood` | String | Mahalle |
| `street` | String | Sokak |
| `full_address` | String | Tam adres |
| `request_count` | Integer | Kümedeki talep sayısı |
| `total_persons_affected` | Integer | Toplam etkilenen kişi |
| `average_priority_score` | Float | Ortalama öncelik puanı |
| `priority_level` | String | Öncelik seviyesi |
| `pending_count` | Integer | Bekleyen talep sayısı |
| `assigned_count` | Integer | Atanmış talep sayısı |
| `resolved_count` | Integer | Çözülmüş talep sayısı |
| `is_noise_cluster` | Integer | Dağınık küme mi (0/1) |
| `status` | Enum | `active` / `resolved` |
| `generated_at` | DateTime | Küme oluşturulma zamanı |

**Desteklenen `need_type` değerleri:**

| Değer | Açıklama |
|-------|----------|
| `arama_kurtarma` | Arama Kurtarma |
| `medikal` | Medikal |
| `yangin` | Yangın Söndürme |
| `enkaz` | Enkaz Kaldırma |
| `su` | Su |
| `barinma` | Barınma |
| `gida` | Gıda |
| `is_makinesi` | İş Makinesi |
| `ulasim` | Ulaşım |

---

## API Endpoint'leri

### `GET /`
Sunucu sağlık kontrolü.

```json
{ "status": "ok", "message": "Afet Koordinasyon API çalışıyor" }
```

---

### `POST /requests`
Yeni talep oluşturur.

**Body:**
```json
{
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal",
  "person_count": 3,
  "description": "Yaralı var, ambulans gerekiyor"
}
```

`person_count` ve `description` opsiyoneldir.

**Yanıt (201):**
```json
{
  "id": "uuid",
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal",
  "person_count": 3,
  "description": "Yaralı var, ambulans gerekiyor",
  "status": "pending",
  "created_at": "2026-03-27T11:00:00Z"
}
```

---

### `GET /requests/prioritized`
Tüm talepleri dinamik öncelik puanına göre sıralı döndürür.

**Yanıt:**
```json
[
  {
    "id": "uuid",
    "latitude": 41.01,
    "longitude": 29.02,
    "need_type": "arama_kurtarma",
    "person_count": 5,
    "description": null,
    "status": "pending",
    "created_at": "2026-03-12T08:00:00Z",
    "dynamic_priority_score": 85.5
  }
]
```

---

### `PATCH /requests/{request_id}/status`
Bir talebin durumunu günceller.

**Body:**
```json
{ "status": "assigned" }
```

Geçerli değerler: `pending`, `assigned`, `resolved`

---

### `POST /requests/task-packages/generate`
Kümeleme algoritmasını çalıştırır, sonuçları DB'ye yazar ve döndürür.

Sadece `status=pending` olan talepler kümelenir. `assigned` veya `resolved` talepler kümelemeye dahil edilmez.

**Yanıt (201):** Oluşturulan kümelerin listesi. Yanıt formatı `GET /task-packages` ile aynıdır (aşağıya bakınız).

---

### `GET /requests/task-packages`
Mevcut kümeleri döndürür.

**Query parametreleri:**
- `need_type` (opsiyonel): İhtiyaç tipine göre filtrele. Örn: `?need_type=su`
- `status` (opsiyonel): Küme durumuna göre filtrele. Varsayılan: `active`
  - `active` — sadece aktif kümeler
  - `resolved` — sadece tamamlanmış kümeler
  - `all` — önce aktifler, sonra tamamlanmışlar (öncelik puanına göre sıralı)

**Yanıt:**
```json
[
  {
    "cluster_id": "uuid",
    "need_type": "yangin",
    "cluster_name": "Kadıköy Osmanağa Mahallesi - Yangın Söndürme Kümesi",
    "center_latitude": 40.990743,
    "center_longitude": 29.028482,
    "location": {
      "district": "Kadıköy",
      "neighborhood": "Osmanağa Mahallesi",
      "street": "Kuşdili Caddesi",
      "full_address": "Kuşdili Caddesi, Osmanağa Mahallesi, Kadıköy"
    },
    "request_count": 30,
    "total_persons_affected": 280,
    "average_priority_score": 20.7,
    "priority_level": "Düşük",
    "status_summary": {
      "pending": 28,
      "assigned": 2,
      "resolved": 0
    },
    "is_noise_cluster": false,
    "status": "active",
    "generated_at": "2026-03-27T11:48:27Z"
  }
]
```

| Alan | Açıklama |
|------|----------|
| `cluster_id` | Kalıcı UUID — takım ataması için kullanılır |
| `cluster_name` | İlçe + mahalle + ihtiyaç tipinden otomatik üretilen ad |
| `total_persons_affected` | Kümedeki tüm taleplerin `person_count` toplamı |
| `average_priority_score` | Kümedeki taleplerin ortalama dinamik öncelik puanı (0-100) |
| `priority_level` | `Kritik` (≥75), `Yüksek` (≥50), `Orta` (≥25), `Düşük` (<25) |
| `status_summary` | Kümedeki taleplerin durum dağılımı |
| `is_noise_cluster` | DBSCAN'ın kümeleyemediği dağınık noktalar için `true` |
| `status` | `active` — yeni oluşturulmuş, `resolved` — tamamlanmış |

---

### `GET /requests/task-packages/{cluster_id}`
Belirli bir kümenin detayını döndürür.

**Yanıt:** Yukarıdaki `TaskPackageResponse` nesnesi.

---

## Öncelik Puanlama Sistemi

### Taban Puanları ve Parametreler

| need_type | Taban Puan | Ağırlık (C_i) | Maks. Tolerans |
|-----------|-----------|---------------|----------------|
| arama_kurtarma | 100 | 0.25 | 6 saat |
| medikal | 95 | 0.20 | 2 saat |
| yangin | 90 | 0.15 | 1 saat |
| enkaz | 80 | 0.12 | 12 saat |
| su | 60 | 0.09 | 72 saat |
| barinma | 50 | 0.07 | 48 saat |
| gida | 40 | 0.06 | 168 saat |
| is_makinesi | 35 | 0.04 | 24 saat |
| ulasim | 25 | 0.02 | 24 saat |

### Zaman Sönümleme Formülü (DPS)

```
P_dynamic(t) = S_base + (S_base × λ × (t / M)) × (1 + C_i)
```

- **λ:** Zaman duyarlılık çarpanı (1.5)
- **t:** Bekleme süresi (saat)
- **M:** Kategorinin maksimum tolerans süresi

Ham puan 1000 ile sınırlandırılır, ardından 0-100 aralığına normalize edilir. Uzun süre bekleyen düşük öncelikli talepler zamanla öne çıkar (kuyruk açlığı önleme).

> Algoritmanın teorik temeli (ÇKKV/AHP + DPS) Google Gemini ile araştırılmış ve tasarlanmıştır. Detaylı dokümana [buradan](https://docs.google.com/document/d/1BdAMHpEGyv_WbslJ7ysQ6LxKDYFSQd_VBGNX3WtlsBE/edit?usp=sharing) ulaşabilirsiniz.

---

## Mekansal Kümeleme (DBSCAN)

`clustering_engine.py` içindeki motor şu adımları izler:

1. Sadece `status=pending` olan talepler alınır
2. Talepler `need_type`'a göre gruplandırılır
3. Her grup için koordinatlar radyana çevrilir
4. DBSCAN `haversine` metriği ile çalışır; `eps = 500m / 6_371_000m ≈ 7.85e-5 radyan`
5. Minimum 2 talep bir küme oluşturur
6. Her küme için merkez koordinat ortalaması alınır, Nominatim ile ters geocoding yapılır
7. `person_count` toplamı ve `status` dağılımı hesaplanır
8. Sonuçlar DB'ye yazılır, her kümeye kalıcı UUID atanır
9. Paketler `average_priority_score`'a göre azalan sırada döndürülür

DBSCAN'ın herhangi bir kümeye atayamadığı noktalar `is_noise_cluster: true` olarak işaretlenir.

---

## Mock Veri Üretici

```bash
# Rastgele 500 kayıt
python mock_data_generator.py

# Kümeleme testi için 10 küme × 30 talep (İstanbul ilçe merkezleri etrafında)
python mock_data_generator.py --clustered
```

---

## Küme Yaşam Döngüsü

1. **Oluşturma:** `POST /task-packages/generate` çağrılır, `pending` talepler kümelenir, DB'ye yazılır
2. **Görüntüleme:** `GET /task-packages` ile aktif kümeler listelenir
3. **Atama:** (Gelecekte) Takım bir kümeye atanır, kümedeki talepler `assigned` olur
4. **Tamamlama:** (Gelecekte) Küme `resolved` olarak işaretlenir
5. **Arşiv:** `GET /task-packages?status=all` ile tamamlanmış kümeler de görüntülenebilir
