import random
import time
from sqlalchemy.orm import Session
from database import SessionLocal
import models

# İstanbul coğrafi sınırları (yaklaşık sınır kutusu)
LAT_MIN, LAT_MAX = 40.8, 41.3
LON_MIN, LON_MAX = 28.6, 29.5

CATEGORIES = ["enkaz", "yangin", "medikal", "gida", "barinma", "su", "is_makinesi", "arama_kurtarma", "ulasim"]

def generate_mock_data(num_records: int = 500):
    db: Session = SessionLocal()

    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {num_records} adet sahte kayıt oluşturuluyor...")

        request_list = []
        for _ in range(num_records):
            request_item = models.AfetzedeTalep(
                need_type=random.choice(CATEGORIES),
                latitude=round(random.uniform(LAT_MIN, LAT_MAX), 6),
                longitude=round(random.uniform(LON_MIN, LON_MAX), 6)
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

if __name__ == "__main__":
    generate_mock_data()
