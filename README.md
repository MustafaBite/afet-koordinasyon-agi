# Afet Koordinasyon Ağı

Afet yönetimi ve koordinasyonu için geliştirilmiş gerçek zamanlı yardım talep sistemi.

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.11+
- Node.js 18+
- PostgreSQL

### Backend Kurulum
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Kurulum
```bash
cd kriz-paneli
npm install
npm run dev
```

## 📁 Proje Yapısı

```
├── backend/              # FastAPI backend
│   ├── routers/         # API endpoints
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   └── test_*.py        # Test files
├── kriz-paneli/         # React frontend
│   └── src/
│       ├── components/  # UI components
│       ├── pages/       # Login, Register
│       ├── services/    # API services
│       └── utils/       # Validation
└── .env                 # Environment variables
```

## 🔑 Özellikler

- ✅ Kullanıcı kimlik doğrulama (JWT)
- ✅ Rol bazlı yetkilendirme
- ✅ Afet talep yönetimi
- ✅ DBSCAN kümeleme algoritması
- ✅ Dinamik önceliklendirme
- ✅ Gerçek zamanlı harita görünümü
- ✅ Takım yönetimi

## 🧪 Testler

```bash
cd backend
python test_auth.py
python test_integration.py
```

## 📚 Dokümantasyon

- [Backend README](backend/README.md)
- [Database Schema](backend/DATABASE_SCHEMA.md)

## 🔐 Environment Variables

`.env` dosyası:
```env
DATABASE_URL="postgresql://user:pass@host:port/db"
SECRET_KEY="your-secret-key"
```