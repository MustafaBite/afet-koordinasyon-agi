from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from typing import List
import models
import schemas
from priority_engine import oncelik_puani_hesapla

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Afet Koordinasyon API çalışıyor"}

@app.post("/talep-gonder", response_model=schemas.AfetzedeTalepResponse)
def create_talep(talep: schemas.AfetzedeTalepCreate, db: Session = Depends(get_db)):
    db_talep = models.AfetzedeTalep(**talep.dict())
    db.add(db_talep)
    db.commit()
    db.refresh(db_talep)
    return db_talep

@app.get("/talepler/oncelikli", response_model=List[schemas.OncelikliTalepResponse])
def get_oncelikli_talepler(db: Session = Depends(get_db)):
    talepler = db.query(models.AfetzedeTalep).all()

    sonuclar = []
    for talep in talepler:
        puan = oncelik_puani_hesapla(talep.need_type)
        sonuclar.append({
            "id": talep.id,
            "latitude": talep.latitude,
            "longitude": talep.longitude,
            "need_type": talep.need_type,
            "created_at": talep.created_at,
            "oncelik_puani": puan
        })

    # En yüksek puanlıdan en düşüğe sırala
    sonuclar.sort(key=lambda x: x["oncelik_puani"], reverse=True)
    return sonuclar
