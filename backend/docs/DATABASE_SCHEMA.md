# Veritabanı Şeması

## Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│  app_users  │────────▶│    teams    │
│             │  N:1    │             │
│ team_id (FK)│         │ id (PK)     │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │ 1:N                   │ 1:N
       │                       │
       ▼                       ▼
┌─────────────────┐    ┌─────────────┐
│disaster_requests│    │  clusters   │
│                 │    │             │
│created_by_id(FK)│    │assigned_team│
│cluster_id (FK)  │───▶│    _id (FK) │
└─────────────────┘ N:1└─────────────┘
```

## Tablolar

### app_users
Sistem kullanıcıları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| email | VARCHAR | Unique, indexed |
| password_hash | VARCHAR | Bcrypt hash |
| first_name | VARCHAR | |
| last_name | VARCHAR | |
| tc_identity_no | VARCHAR(11) | Unique, indexed |
| phone | VARCHAR(11) | 05xxxxxxxxx |
| role | VARCHAR | citizen, volunteer, coordinator, admin |
| expertise_area | VARCHAR | Nullable |
| organization | VARCHAR | Nullable |
| city | VARCHAR | |
| district | VARCHAR | |
| profile_photo_url | VARCHAR | Nullable |
| is_active | BOOLEAN | Default: true |
| created_at | TIMESTAMP | UTC |
| team_id | UUID | FK → teams.id, nullable |

### disaster_requests
Afet yardım talepleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| latitude | FLOAT | |
| longitude | FLOAT | |
| need_type | VARCHAR | |
| person_count | INTEGER | Default: 1 |
| description | VARCHAR | Nullable |
| status | ENUM | pending, assigned, resolved |
| is_verified | BOOLEAN | Deprem bölgesine yakınlık |
| created_at | TIMESTAMP | UTC |
| created_by_user_id | UUID | FK → app_users.id, nullable |
| cluster_id | UUID | FK → clusters.id, nullable |

### clusters
DBSCAN ile oluşturulan talep kümeleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| need_type | VARCHAR | |
| cluster_name | VARCHAR | Otomatik üretilen |
| center_latitude | FLOAT | |
| center_longitude | FLOAT | |
| district | VARCHAR | Nullable |
| neighborhood | VARCHAR | Nullable |
| street | VARCHAR | Nullable |
| full_address | VARCHAR | Nullable |
| request_count | INTEGER | |
| total_persons_affected | INTEGER | |
| average_priority_score | FLOAT | 0-100 |
| priority_level | VARCHAR | Kritik, Yüksek, Orta, Düşük |
| pending_count | INTEGER | Default: 0 |
| assigned_count | INTEGER | Default: 0 |
| resolved_count | INTEGER | Default: 0 |
| is_noise_cluster | INTEGER | 0 veya 1 |
| status | ENUM | active, resolved |
| generated_at | TIMESTAMP | UTC |
| assigned_team_id | UUID | FK → teams.id, nullable |

### anomaly_events
Supheli cihaz davranislari ve guvenlik audit kayitlari.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| event_type | VARCHAR | Olay tipi, or. `register_multi_identity_spike` |
| device_key | VARCHAR | `IP + User-Agent` tabanli cihaz anahtari |
| ip_address | VARCHAR | Istek IP adresi |
| user_agent | VARCHAR | Istek user-agent bilgisi |
| request_path | VARCHAR | Olayin tetiklendigi endpoint |
| action_taken | VARCHAR | blocked, logged vb. |
| reason | VARCHAR | Audit aciklamasi |
| observed_identifier | VARCHAR | Maskelenmis kimlik degeri |
| distinct_value_count | INTEGER | Pencere icindeki benzersiz deger sayisi |
| window_seconds | INTEGER | Kuralin calistigi zaman penceresi |
| created_at | TIMESTAMP | UTC |

### teams
Saha ekipleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| team_name | VARCHAR | |
| capacity | INTEGER | |
| location | VARCHAR | Nullable |
| created_at | TIMESTAMP | UTC |

## Foreign Key İlişkileri

| Tablo | Kolon | Referans | Açıklama |
|-------|-------|----------|----------|
| app_users | team_id | teams.id | Kullanıcının takımı |
| disaster_requests | created_by_user_id | app_users.id | Talebi oluşturan |
| disaster_requests | cluster_id | clusters.id | Talebin kümesi |
| clusters | assigned_team_id | teams.id | Kümeye atanan takım |

**Not:** Tüm FK'ler `ON DELETE SET NULL` ile tanımlı.

## İş Akışı

1. **Kullanıcı Kaydı** → app_users tablosuna eklenir
2. **Supheli Kayit Denemesi** → anomaly_events tablosuna audit kaydi dusulur, istek bloke edilir
3. **Talep Oluşturma** → disaster_requests tablosuna eklenir (status: pending)
4. **Kümeleme** → Pending talepler DBSCAN ile kümelenir, yuk altinda hizli gorev paketi moduna da gecebilir
5. **Takım Atama** → Coordinator bir kümeye takım atar (clusters.assigned_team_id)
6. **Görev Tamamlama** → Talepler resolved olur, küme resolved olur
