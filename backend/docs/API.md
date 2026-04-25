# API Dokümantasyonu

Afet Koordinasyon Sistemi REST API referansı.

## 📍 Base URL
```
http://localhost:8000
```

**Interaktif Dokümantasyon:**
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📚 İçindekiler
1. [Authentication](#authentication-endpoints)
2. [Disaster Requests](#disaster-request-endpoints)
3. [Clusters (Task Packages)](#cluster-endpoints)
4. [Vehicles](#vehicle-endpoints)
5. [Reference Data](#reference-data)

---

## Authentication Endpoints

### POST /auth/register
Yeni kullanıcı kaydı.

**Guvenlik davranisi:**
- Ayni cihazdan (`IP + User-Agent`) kisa surede 10 farkli `tc_identity_no` ile kayit denemesi gelirse istek `403` ile reddedilir.
- Supheli denemeler `anomaly_events` audit kayitlarina yazilir.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Ahmet",
  "last_name": "Yılmaz",
  "tc_identity_no": "12345678901",
  "phone": "05551234567",
  "role": "volunteer",
  "expertise_area": "medikal",
  "organization": "Kızılay",
  "city": "İstanbul",
  "district": "Kadıköy",
  "profile_photo_url": "https://example.com/photo.png"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Ahmet",
    "role": "volunteer"
  }
}
```

### POST /auth/login
Kullanıcı girişi.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):** Register ile aynı format.

### GET /auth/me
Mevcut kullanıcı bilgisi (JWT token gerekli).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Ahmet",
  "last_name": "Yılmaz",
  "role": "volunteer",
  "team_id": "uuid"
}
```

---

## Disaster Request Endpoints

### GET /
Sunucu sağlık kontrolü.

**Response:**
```json
{
  "message": "Afet Koordinasyon API çalışıyor"
}
```

### POST /requests
Yeni talep oluşturur.

**Request:**
```json
{
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal",
  "person_count": 3,
  "description": "Yaralı var, ambulans gerekiyor"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "latitude": 41.0082,
  "longitude": 28.9784,
  "need_type": "medikal",
  "person_count": 3,
  "description": "Yaralı var, ambulans gerekiyor",
  "status": "pending",
  "created_at": "2026-03-27T11:00:00Z",
  "is_verified": false
}
```

### GET /requests/prioritized
Tüm talepleri dinamik öncelik puanına göre sıralı döndürür.

**Response:**
```json
[
  {
    "id": "uuid",
    "latitude": 41.01,
    "longitude": 29.02,
    "need_type": "arama_kurtarma",
    "person_count": 5,
    "status": "pending",
    "created_at": "2026-03-12T08:00:00Z",
    "is_verified": true,
    "dynamic_priority_score": 85.5
  }
]
```

### PATCH /requests/{request_id}/status
Bir talebin durumunu günceller.

**Request:**
```json
{
  "status": "assigned"
}
```

**Valid values:** `pending`, `assigned`, `resolved`

---

## Cluster Endpoints

### POST /requests/task-packages/generate
Kümeleme algoritmasını çalıştırır ve sonuçları döndürür.

**Graceful degradation:**
- Bekleyen talep sayisi `100000+` olursa veya kompleks kumeleme guvenli sure butcesini asarsa sistem DBSCAN yerine hizli gorev paketi moduna gecer.
- Hızlı mod yine ayni response seklini dondurur, ancak sonuc listesi en acil gorevleri temsil eden yalniz gorev paketlerinden olusur.
- Overload modunda en fazla `500` hizli gorev paketi materialize edilir.

**Response (201):** Oluşturulan kümelerin listesi.

### GET /requests/task-packages
Mevcut kümeleri döndürür.

**Query Parameters:**
- `need_type` (optional): İhtiyaç tipine göre filtrele
- `status` (optional): `active`, `resolved`, `all` (default: `active`)

**Response:**
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

### GET /requests/task-packages/{cluster_id}
Belirli bir kümenin detayını döndürür.

### GET /requests/task-packages/{cluster_id}/recommend-vehicles
**Otonom Araç Önerisi Sistemi**

Bir küme için en uygun araçları AI ile önerir. Çok kriterli karar verme (MCDM) algoritması kullanır.

**Query Parameters:**
- `top_n` (optional): Kaç araç önerilecek (default: 3, max: 10)

**Response (200):**
```json
[
  {
    "vehicle_id": "uuid",
    "vehicle_type": "Kamyon",
    "capacity": "10 Ton",
    "latitude": 41.0082,
    "longitude": 28.9784,
    "base_speed_kmh": 60,
    "score": 87.5,
    "details": {
      "distance_km": 5.2,
      "eta_minutes": 8,
      "available_stock": 100,
      "required_quantity": 50,
      "stock_score": 100.0,
      "distance_score": 85.3,
      "speed_score": 75.0,
      "urgency_score": 82.5,
      "total_score": 87.5
    },
    "recommendation_text": "🎯 ÖNERİLEN ARAÇ: Bu kümenin 50 çadır ihtiyacı var. En yakın ve stokta en az 50 çadır olan araç: Kamyon (10 Ton). Mesafe: 5.2 km, Tahmini Varış: 8 dakika. Mevcut Stok: 100 çadır. ⭐ Skor: 87.5/100"
  }
]
```

**Algoritma Kriterleri:**
- **Aciliyet (40%)**: Kümenin öncelik skoru
- **Mesafe (27%)**: Araç-küme arası mesafe (ETA)
- **Stok (18%)**: Stok yeterliliği
- **Hız (15%)**: Araç hızı

**Hata Durumları:**
- `404`: Cluster bulunamadı
- `404`: Uygun araç bulunamadı (stok yetersiz)

### POST /requests/task-packages/{cluster_id}/assign-vehicle
**Araç Atama ve ETA Hesaplama**

Bir aracı kümeye atar, stok günceller ve ETA (Tahmini Varış Süresi) hesaplar.

**Query Parameters:**
- `vehicle_id` (required): Atanacak aracın UUID'si

**Response (200):**
```json
{
  "message": "Araç başarıyla atandı",
  "cluster_id": "uuid",
  "vehicle_id": "uuid",
  "remaining_stock": 50,
  "distance_km": 5.2,
  "eta_minutes": 8,
  "cluster_status": "resolved"
}
```

**ETA Hesaplama Formülü:**
```
ETA (dakika) = (Mesafe × Afet Düzeltme Katsayısı) / Araç Hızı × 60
```

- Afet Düzeltme Katsayısı: 1.2 (yol koşulları)
- Kritik durumlarda (priority ≥75) hız %10 artırılır

**Hata Durumları:**
- `404`: Cluster veya araç bulunamadı
- `400`: Yetersiz stok

---

## Vehicle Endpoints

### POST /api/vehicles
Yeni araç ekler.

**Request:**
```json
{
  "latitude": 41.0082,
  "longitude": 28.9784,
  "vehicle_type": "Kamyon",
  "capacity": "10 Ton",
  "base_speed_kmh": 60
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "latitude": 41.0082,
  "longitude": 28.9784,
  "vehicle_type": "Kamyon",
  "capacity": "10 Ton",
  "base_speed_kmh": 60,
  "tent_count": 0,
  "food_count": 0,
  "water_count": 0,
  "medical_count": 0,
  "blanket_count": 0,
  "created_at": "2026-03-27T12:00:00Z"
}
```

### GET /api/vehicles
Tüm araçları listeler.

### GET /api/vehicles/{vehicle_id}
Belirli bir aracı getirir.

### PUT /api/vehicles/{vehicle_id}
Araç bilgilerini günceller (stok dahil).

**Request:**
```json
{
  "tent_count": 100,
  "food_count": 200,
  "water_count": 500,
  "medical_count": 50,
  "blanket_count": 150,
  "base_speed_kmh": 65
}
```

### DELETE /api/vehicles/{vehicle_id}
Aracı siler.

---

## Vehicle Types & Speeds

| Araç Tipi | Varsayılan Hız (km/h) |
|-----------|------------------------|
| Ambulans | 70 |
| Kamyon | 60 |
| İtfaiye | 65 |
| Su Tankeri | 55 |
| İş Makinesi | 30 |

---

## Need Types

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

## User Roles

| Rol | Açıklama |
|-----|----------|
| `citizen` | Vatandaş (sadece talep oluşturabilir) |
| `volunteer` | Gönüllü (saha çalışanı) |
| `coordinator` | Koordinatör (takım yöneticisi) |
| `admin` | Sistem yöneticisi |

## Priority Levels

| Seviye | Puan Aralığı |
|--------|--------------|
| Kritik | ≥75 |
| Yüksek | 50-74 |
| Orta | 25-49 |
| Düşük | <25 |
