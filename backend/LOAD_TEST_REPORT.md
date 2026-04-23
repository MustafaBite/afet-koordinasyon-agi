# Yük Testi Raporu — RESQ Afet Koordinasyon API

**Görev 5.1 — Load Testing**  
**Tarih:** 23 Nisan 2026  
**Araç:** [Locust](https://locust.io/) v2.43.4  
**Test Dosyası:** `locustfile.py`

---

## Test 1 — Normal Yük (50 Kullanıcı)

### Koşullar

| Parametre | Değer |
|-----------|-------|
| Toplam sanal kullanıcı | 50 |
| Kullanıcı ekleme hızı | 5 kullanıcı/saniye |
| Test süresi | 60 saniye |
| Sunucu | Geliştirme ortamı (tek çekirdek, uvicorn) |

### Sonuçlar

| Endpoint | İstek | Hata | Ort. (ms) | Medyan (ms) | 95% (ms) | req/s |
|----------|-------|------|-----------|-------------|----------|-------|
| POST /talep-gonder | 675 | **0** | 83 | **3** | 17 | 11.6 |
| GET /requests/prioritized | 425 | **0** | 920 | 690 | 2.100 | 7.3 |
| GET /requests/task-packages | 218 | **0** | 813 | 520 | 2.000 | 3.7 |
| GET /araclar | 219 | **0** | 819 | 580 | 2.000 | 3.7 |
| **Toplam** | **1.559** | **0 (%0)** | **519** | **330** | **1.900** | **26.4** |

**Sonuç: ✅ Sistem kararlı çalıştı. Sıfır hata.**

---

## Test 2 — Stres Testi (500 Kullanıcı / Felaket Senaryosu)

### Koşullar

| Parametre | Değer |
|-----------|-------|
| Toplam sanal kullanıcı | **500** |
| Kullanıcı ekleme hızı | 25 kullanıcı/saniye |
| Test süresi | 120 saniye |
| Sunucu | Geliştirme ortamı (tek çekirdek, uvicorn) |

### Sonuçlar

| Endpoint | İstek | Hata | Hata Oranı | Ort. (ms) | Medyan (ms) |
|----------|-------|------|------------|-----------|-------------|
| POST /talep-gonder | 4.331 | 4.331 | **%100** | 4.095 | 4.100 |
| GET /requests/prioritized | 2.917 | 2.917 | **%100** | 4.094 | 4.100 |
| GET /requests/task-packages | 1.454 | 1.454 | **%100** | 4.095 | 4.100 |
| GET /araclar | 1.407 | 1.407 | **%100** | 4.094 | 4.100 |
| **Toplam** | **10.109** | **10.109** | **%100** | **4.095** | **4.100** |

**Hata Türü:** `HTTP 0` — Bağlantı zaman aşımı (connection timeout). Sunucu yanıt vermedi.

**Sonuç: ❌ Sistem 500 eş zamanlı kullanıcıda çöktü.**

---

## Analiz

### Neden Çöktü?

500 kullanıcı aynı anda bağlandığında tüm yanıtlar tam olarak **~4.100 ms** aldı ve hepsi `HTTP 0` (bağlantı koptu) hatası verdi. Bu, sunucunun bağlantı kuyruğunu (connection queue) doldurduğunu ve yeni bağlantıları reddettiğini gösteriyor.

**Temel Neden:** Geliştirme ortamında `uvicorn` tek çekirdekte çalışıyor. Her istek Kandilli API'sine dış çağrı yapıyor (cross-check), bu da her isteği ~100-500ms bloke ediyor. 500 kullanıcı aynı anda gelince kuyruk doldu.

### Kapasite Sınırı

| Kullanıcı Sayısı | Durum | Hata Oranı | Ort. Yanıt |
|-----------------|-------|------------|-----------|
| 50 | ✅ Kararlı | %0 | 519 ms |
| 500 | ❌ Çöküş | %100 | 4.095 ms |
| **Eşik** | **~50-100 kullanıcı arası** | — | — |

---

## Production İçin Öneriler

Gerçek bir afet anında sistemi ayakta tutmak için aşağıdaki iyileştirmeler yapılmalıdır:

### 1. Çoklu Worker (Hızlı Çözüm)
```bash
# Tek çekirdek yerine 4 worker ile çalıştır
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```
Bu değişiklik kapasiteyi yaklaşık 4x artırır.

### 2. Kandilli API Çağrısını Arka Plana Al
Şu an her ihbar geldiğinde Kandilli API'si senkron olarak çağrılıyor. Bu çağrı arka planda (background task) yapılırsa ihbar anında kaydedilir, doğrulama sonradan güncellenir.

### 3. Redis ile Önbellekleme
Kandilli verisi her istek için çekilmek yerine 60 saniyede bir Redis'e yazılabilir. Tüm istekler Redis'ten okur — dış API çağrısı ortadan kalkar.

### 4. Load Balancer + Yatay Ölçekleme
Docker Compose ile birden fazla backend instance çalıştırılıp Nginx ile yük dağıtılabilir.

---

## Testi Yeniden Çalıştırmak

```bash
# Test 1 — Normal yük (50 kullanıcı, 60 saniye)
locust -f locustfile.py --headless -u 50 -r 5 --run-time 60s --host http://localhost:8000

# Test 2 — Stres testi (500 kullanıcı, 120 saniye)
locust -f locustfile.py --headless -u 500 -r 25 --run-time 120s --host http://localhost:8000

# Görsel arayüzle (tarayıcıdan http://localhost:8089)
locust -f locustfile.py --host http://localhost:8000
```
