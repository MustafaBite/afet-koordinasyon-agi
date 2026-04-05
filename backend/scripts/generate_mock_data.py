import random
import time
from sqlalchemy.orm import Session
from database import SessionLocal
import models

# İstanbul coğrafi sınırları (yaklaşık sınır kutusu)
LAT_MIN, LAT_MAX = 40.8, 41.3
LON_MIN, LON_MAX = 28.6, 29.5

CATEGORIES = ["enkaz", "yangin", "medikal", "gida", "barinma", "su", "is_makinesi", "arama_kurtarma", "ulasim"]

# Kümeleme testi için bilinen merkez noktaları (İstanbul ilçeleri)
CLUSTER_CENTERS = [
    (41.0082, 28.9784),  # Fatih
    (40.9903, 29.0295),  # Kadıköy
    (41.0430, 29.0090),  # Beşiktaş
    (41.0766, 29.0510),  # Sarıyer
    (40.9628, 29.0927),  # Maltepe
    (41.0050, 28.8970),  # Bakırköy
    (41.0600, 28.9200),  # Eyüpsultan
    (40.9200, 29.1900),  # Tuzla
    (41.1050, 29.0250),  # Beykoz
    (40.9870, 29.1560),  # Ataşehir
]

def generate_mock_data(num_records: int = 500):
    db: Session = SessionLocal()

    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {num_records} adet sahte kayıt oluşturuluyor...")

        request_list = []
        for _ in range(num_records):
            request_item = models.DisasterRequest(
                need_type=random.choice(CATEGORIES),
                latitude=round(random.uniform(LAT_MIN, LAT_MAX), 6),
                longitude=round(random.uniform(LON_MIN, LON_MAX), 6),
                person_count=random.randint(1, 20),
            )
            request_list.append(request_item)

        db.add_all(request_list)
        db.commit()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {num_records} kayıt başarıyla veritabanına eklendi.")

    except Exception as e:
        db.rollback()
        print(f"Hata oluştu: {e}")
    finally:
        db.close()


def generate_clustered_mock_data(num_clusters: int = 10, requests_per_cluster: int = 30):
    """
    Kümeleme testi için yoğunlaştırılmış mock data üretir.
    Her küme, bilinen bir merkez noktası etrafında 500m yarıçapta
    aynı tip taleplerin yoğunlaştığı veridir.
    """
    db: Session = SessionLocal()

    # 500m ≈ 0.0045 derece (enlem için yaklaşık)
    SPREAD_DEG = 0.0045

    try:
        total = num_clusters * requests_per_cluster
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {num_clusters} küme x {requests_per_cluster} talep = {total} kümelenmiş kayıt oluşturuluyor...")

        request_list = []
        for i in range(num_clusters):
            center = CLUSTER_CENTERS[i % len(CLUSTER_CENTERS)]
            need_type = CATEGORIES[i % len(CATEGORIES)]

            for _ in range(requests_per_cluster):
                lat = round(center[0] + random.uniform(-SPREAD_DEG, SPREAD_DEG), 6)
                lon = round(center[1] + random.uniform(-SPREAD_DEG, SPREAD_DEG), 6)

                request_item = models.DisasterRequest(
                    need_type=need_type,
                    latitude=lat,
                    longitude=lon,
                    person_count=random.randint(1, 20),
                )
                request_list.append(request_item)

        db.add_all(request_list)
        db.commit()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {total} kümelenmiş kayıt başarıyla veritabanına eklendi.")

    except Exception as e:
        db.rollback()
        print(f"Hata oluştu: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clustered":
        generate_clustered_mock_data()
    else:
        generate_mock_data()
