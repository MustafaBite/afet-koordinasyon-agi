"""
Görev 5.1 — Yük Testi (Load Testing)
RESQ Afet Koordinasyon API — Locust Yük Test Senaryosu

Çalıştırmak için:
    locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost:8000

Parametreler:
    -u 100      : Toplam 100 sanal kullanıcı
    -r 10       : Saniyede 10 kullanıcı ekle (ramp-up)
    --run-time  : Test süresi
    --host      : Hedef sunucu
"""

import random
from locust import HttpUser, task, between

# Test için kullanılacak örnek koordinatlar (Türkiye'nin farklı bölgeleri)
KOORDINATLAR = [
    (41.01, 29.02),   # İstanbul
    (39.92, 32.85),   # Ankara
    (38.42, 27.14),   # İzmir
    (37.00, 35.32),   # Adana
    (40.19, 29.06),   # Bursa
    (39.74, 37.01),   # Sivas
    (37.87, 32.49),   # Konya
    (36.89, 30.70),   # Antalya
    (39.73, 43.05),   # Erzurum
    (41.29, 36.35),   # Samsun
]

IHTIYAC_TURLERI = [
    "arama_kurtarma", "medikal", "yangin",
    "enkaz", "su", "barinma", "gida",
    "is_makinesi", "ulasim"
]


class AfetKullanicisi(HttpUser):
    """
    Gerçek bir afet anında sisteme bağlanan kullanıcıyı simüle eder.
    Her kullanıcı ihbar gönderir ve öncelikli listeyi sorgular.
    """
    wait_time = between(0.5, 2)  # İstekler arası 0.5-2 saniye bekleme

    @task(3)
    def ihbar_gonder(self):
        """
        En sık yapılan işlem: yeni ihbar gönderme.
        Ağırlık 3 — diğer görevlere göre 3x daha sık çalışır.
        """
        lat, lon = random.choice(KOORDINATLAR)
        # Koordinata küçük rastgele sapma ekle (gerçekçilik için)
        lat += random.uniform(-0.5, 0.5)
        lon += random.uniform(-0.5, 0.5)

        payload = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "need_type": random.choice(IHTIYAC_TURLERI),
            "person_count": random.randint(1, 50),
            "description": "Yük testi simülasyonu",
        }

        with self.client.post(
            "/talep-gonder",
            json=payload,
            catch_response=True,
            name="POST /talep-gonder",
        ) as response:
            if response.status_code == 201 or response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limit — beklenen davranış, hata sayma
                response.success()
            else:
                response.failure(f"Beklenmeyen HTTP {response.status_code}")

    @task(2)
    def oncelikli_listele(self):
        """
        Öncelikli ihbar listesini çek.
        Ağırlık 2 — ihbar gönderme kadar sık.
        """
        with self.client.get(
            "/requests/prioritized",
            catch_response=True,
            name="GET /requests/prioritized",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list):
                    response.failure("Liste dönmedi")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def araclari_listele(self):
        """
        Araç listesini çek.
        Ağırlık 1 — en az sık yapılan işlem.
        """
        with self.client.get(
            "/araclar",
            catch_response=True,
            name="GET /araclar",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def kumeleri_listele(self):
        """Küme listesini çek."""
        with self.client.get(
            "/requests/task-packages",
            catch_response=True,
            name="GET /requests/task-packages",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
