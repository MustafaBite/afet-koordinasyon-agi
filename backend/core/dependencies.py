"""
Merkezi FastAPI bağımlılıkları (Dependency Injection).

Tüm router'lar buradan import eder; mantık tek yerde durur.
"""
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # noqa: F401
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import SessionLocal

# ─── Veritabanı ────────────────────────────────────────────────────────────

def get_db():
    """Veritabanı oturumu üretir; kullanım bittikten sonra kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── JWT / Kimlik Doğrulama ────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM  = "HS256"

oauth2_scheme          = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Bearer token'dan aktif kullanıcıyı döndürür.
    Token eksik veya geçersizse 401 fırlatır.
    """
    import models  # döngüsel import önlemek için yerel

    hata = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise hata
    except JWTError:
        raise hata

    kullanici = db.query(models.User).filter(models.User.email == email).first()
    if kullanici is None:
        raise hata
    return kullanici


def require_coordinator(
    current_user=Depends(get_current_user),
):
    """Koordinatör veya yönetici rolü zorunlu."""
    if current_user.role not in ("coordinator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Koordinatör veya yönetici rolü gereklidir",
        )
    return current_user


def require_admin(
    current_user=Depends(get_current_user),
):
    """Yalnızca yönetici rolü kabul edilir."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yönetici rolü gereklidir",
        )
    return current_user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    """
    Bearer token varsa kullanıcıyı döndürür, yoksa None döner.
    Token geçersizse 401 fırlatır.
    """
    if token is None:
        return None
    return get_current_user(token=token, db=db)
