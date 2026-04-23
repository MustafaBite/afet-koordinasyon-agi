import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # Her worker için maksimum 5 kalıcı bağlantı
    max_overflow=5,     # Gerekirse 5 ekstra bağlantı açılabilir (toplam 10/worker)
    pool_timeout=30,    # Bağlantı beklerken 30 saniye timeout
    pool_recycle=1800,  # 30 dakikada bir bağlantıları yenile (kopuk bağlantı önleme)
    pool_pre_ping=True, # Her kullanımdan önce bağlantıyı test et
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

