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

## Dosya Yapısı ve Görevleri

*   **`main.py`**: Ana FastAPI uygulaması ve uç noktalar (Örn: `/talep-gonder` POST endpoint'i).
*   **`database.py`**: SQLAlchemy ile PostgreSQL veritabanı bağlantısı ayarları.
*   **`models.py`**: Veritabanı tablolarının SQLAlchemy modelleri (Örn: `afetzede_talepleri` tablosu).
*   **`schemas.py`**: Gelen/Giden verilerin Pydantic ile doğrulama şemaları.
*   **`mock_data_generator.py`**: Yapay zeka eğitiminde kullanılmak üzere veritabanına İstanbul sınırlarında rastgele sahte çağrı (su, medikal vb.) verileri ekleyen bot (Çalıştırmak için: `python mock_data_generator.py`).
*   **`live_earthquake_data.py`**: Kandilli Rasathanesi API'si üzerinden son depremleri çeken bağımsız script.