# API Dokümantasyonu

## Base URL
```
http://localhost:8000
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Authentication Endpoints

### POST /auth/register
Yeni kullanıcı kaydı.

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
