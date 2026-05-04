"""
Supabase Storage entegrasyonu — fotoğraf / ses dosyası yükleme.

Ortam değişkenleri:
  SUPABASE_URL         = https://<project-id>.supabase.co
  SUPABASE_SERVICE_KEY = service_role secret key
"""

import os
import uuid
import httpx
from fastapi import HTTPException

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET = "resq-photos"

_ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/heic",
    "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/aac",
}
MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def _storage_headers() -> dict:
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
    }


def _public_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"


def upload_file(content: bytes, content_type: str, folder: str = "photos") -> str:
    """
    Dosyayı Supabase Storage'a yükler ve public URL döndürür.
    Hata durumunda HTTPException fırlatır.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Storage servisi yapılandırılmamış (SUPABASE_URL / SUPABASE_SERVICE_KEY eksik)",
        )

    if content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Desteklenmeyen dosya türü: {content_type}",
        )

    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu 20 MB sınırını aşıyor ({len(content) // 1024} KB)",
        )

    ext = content_type.split("/")[-1].replace("jpeg", "jpg")
    object_name = f"{folder}/{uuid.uuid4()}.{ext}"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{object_name}"

    try:
        response = httpx.put(
            upload_url,
            content=content,
            headers={
                **_storage_headers(),
                "Content-Type": content_type,
            },
            timeout=30,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Storage bağlantı hatası: {exc}")

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Storage yükleme başarısız: {response.status_code} — {response.text[:200]}",
        )

    return _public_url(object_name)
