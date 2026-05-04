from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

import models
import schemas
from core.dependencies import get_db, get_current_user, get_optional_user, require_coordinator
from rate_limiter import check_rate_limit
from services.priority import calculate_dynamic_priority
from services.request_intake import create_disaster_request
from services.storage import upload_file

router = APIRouter(tags=["requests"])


# ─── Yardımcı: model → dict dönüşümü ──────────────────────────────────────

def _to_prioritized(req: models.DisasterRequest) -> dict:
    score = calculate_dynamic_priority(req.need_type, req.created_at)
    return {
        "id":                     req.id,
        "latitude":               req.latitude,
        "longitude":              req.longitude,
        "need_type":              req.need_type,
        "person_count":           req.person_count,
        "description":            req.description,
        "status":                 req.status,
        "created_at":             req.created_at,
        "is_verified":            req.is_verified,
        "created_by_user_id":     req.created_by_user_id,
        "dynamic_priority_score": score,
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.RequestResponse, status_code=201)
def create_request(
    body: schemas.RequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_optional_user),
    _: None = Depends(check_rate_limit),
):
    """Yeni afet ihbarı oluşturur. Giriş yapılmışsa kullanıcıya bağlar."""
    result = create_disaster_request(
        db,
        body,
        client_ip=request.client.host if request.client else "unknown",
        created_by_user_id=current_user.id if current_user else None,
    )
    return result.disaster_request


@router.get("/mine", response_model=List[schemas.PrioritizedRequestResponse])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Giriş yapan kullanıcıya ait tüm talepleri döndürür (en yeni önce)."""
    reqs = (
        db.query(models.DisasterRequest)
        .filter(models.DisasterRequest.created_by_user_id == current_user.id)
        .order_by(models.DisasterRequest.created_at.desc())
        .all()
    )
    return [_to_prioritized(r) for r in reqs]


@router.get("/prioritized", response_model=List[schemas.PrioritizedRequestResponse])
def get_prioritized(db: Session = Depends(get_db)):
    """Tüm talepleri dinamik öncelik puanına göre sıralı döndürür (personel paneli)."""
    all_requests = db.query(models.DisasterRequest).all()
    results = [_to_prioritized(r) for r in all_requests]
    results.sort(key=lambda x: (-x["dynamic_priority_score"], x["created_at"]))
    return results


@router.patch("/{request_id}/status", response_model=schemas.RequestResponse)
def update_status(
    request_id: UUID,
    body: schemas.StatusUpdate,
    db: Session = Depends(get_db),
):
    """Talebin durumunu günceller."""
    req = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    req.status = body.status
    db.commit()
    db.refresh(req)
    return req


@router.get("/dogrulanmamis")
def get_dogrulanmamis_ihbarlar(
    oncelik: str = Query(None),
    db: Session = Depends(get_db),
):
    """Doğrulanmamış ihbarları listeler. Koordinatör paneli için."""
    query = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.is_verified == False  # noqa: E712
    )
    if oncelik:
        query = query.filter(models.DisasterRequest.need_type == oncelik)
    return query.all()


@router.post("/{request_id}/dogrula")
def verify_request(request_id: UUID, db: Session = Depends(get_db), _: models.User = Depends(require_coordinator)):
    """İhbarı doğrulanmış olarak işaretler."""
    req = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı")
    req.is_verified = True
    db.commit()
    return {"durum": "başarılı", "mesaj": "İhbar doğrulandı."}


@router.post("/{request_id}/reddet")
def reject_request(request_id: UUID, db: Session = Depends(get_db), _: models.User = Depends(require_coordinator)):
    """İhbarı reddeder ve siler."""
    req = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı")
    db.delete(req)
    db.commit()
    return {"durum": "başarılı", "mesaj": "İhbar silindi."}


@router.post("/{request_id}/photos")
async def upload_photos(
    request_id: UUID,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Bir ihbara ait fotoğraf/ses dosyalarını Supabase Storage'a yükler.
    Yüklenen public URL'ler DB'de photo_urls/audio_url alanına eklenir.
    """
    req = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı")

    if len(files) > 5:
        raise HTTPException(status_code=400, detail="En fazla 5 dosya yüklenebilir")

    new_photo_urls = list(req.photo_urls or [])
    new_audio_url = req.audio_url

    for file in files:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        is_audio = content_type.startswith("audio/")
        folder = "audio" if is_audio else "photos"
        public_url = upload_file(content, content_type, folder=folder)

        if is_audio:
            new_audio_url = public_url
        else:
            new_photo_urls.append(public_url)

    req.photo_urls = new_photo_urls
    req.audio_url = new_audio_url
    db.commit()
    db.refresh(req)

    return {
        "request_id": str(req.id),
        "photo_urls": req.photo_urls,
        "audio_url": req.audio_url,
    }


@router.get("/istatistikler")
def get_stats(db: Session = Depends(get_db)):
    """Toplam, doğrulanan ve bekleyen ihbar istatistiklerini döndürür."""
    toplam     = db.query(models.DisasterRequest).count()
    dogrulanan = db.query(models.DisasterRequest).filter(
        models.DisasterRequest.is_verified == True  # noqa: E712
    ).count()
    bekleyen = toplam - dogrulanan
    return {
        "toplam_ihbar":    toplam,
        "dogrulanan_ihbar": dogrulanan,
        "bekleyen_ihbar":  bekleyen,
        "basari_orani":    f"{(dogrulanan / toplam) * 100:.2f}%" if toplam > 0 else "0%",
    }
