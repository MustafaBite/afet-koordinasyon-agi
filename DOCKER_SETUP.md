# Docker Kurulum Rehberi

## 🐳 Hızlı Başlangıç

### Gereksinimler
- Docker Desktop (Windows/Mac) veya Docker Engine (Linux)
- Docker Compose v2.0+

### Kurulum

```bash
# Projeyi klonla
git clone <repo-url>
cd afet-koordinasyon-agi

# Tüm servisleri başlat (PostgreSQL + Backend + Frontend)
docker-compose up -d

# Logları izle
docker-compose logs -f
```

### Erişim
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Temel Komutlar

```bash
# Başlat
docker-compose up -d

# Durdur
docker-compose down

# Veritabanı ile birlikte temizle
docker-compose down -v

# Logları izle
docker-compose logs -f backend
docker-compose logs -f frontend

# Yeniden başlat
docker-compose restart

# Container'a bağlan
docker-compose exec backend bash
docker-compose exec db psql -U afet_user -d afet_koordinasyon
```

## 🔧 Yapılandırma

### Port Değiştirme
`docker-compose.yml` dosyasında:
```yaml
ports:
  - "8080:8000"  # Backend
  - "3000:5173"  # Frontend
```

### Ortam Değişkenleri
```yaml
environment:
  DATABASE_URL: postgresql://user:pass@db:5432/db_name
  SECRET_KEY: your-secret-key
```

## 🐛 Sorun Giderme

**Port çakışması:**
```bash
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000
```

**Veritabanı hatası:**
```bash
docker-compose down -v
docker-compose up -d
```

**Yeniden build:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🔐 Production Notları

- `SECRET_KEY` değiştirin
- Güçlü veritabanı şifresi kullanın
- `.env` dosyası ile hassas bilgileri yönetin
- HTTPS kullanın (Nginx reverse proxy)
- `restart: always` ekleyin

## 📝 Notlar

- Hot-reload aktif (kod değişiklikleri otomatik yansır)
- Veritabanı verileri `postgres_data` volume'ünde kalıcı
- Container'lar arası iletişim Docker network üzerinden
