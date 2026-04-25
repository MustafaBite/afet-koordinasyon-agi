from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os

# JWT ve şifreleme için gerekli importlar (kurulum gerekebilir)
try:
    from jose import JWTError, jwt
    import bcrypt
except ImportError:
    raise ImportError("Lütfen şu paketleri yükleyin: pip install python-jose[cryptography] bcrypt")

import models
import schemas
from core.dependencies import get_db
from services.anomaly_detection import guard_against_tc_rotation

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT ayarları

# JWT ayarları
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 gün

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: schemas.UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    guard_against_tc_rotation(db, request, user_data.tc_identity_no)

    # E-posta kontrolü
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kayıtlı"
        )
    
    # TC Kimlik kontrolü
    existing_tc = db.query(models.User).filter(models.User.tc_identity_no == user_data.tc_identity_no).first()
    if existing_tc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu TC Kimlik No zaten kayıtlı"
        )
    
    # Şifreyi hashle
    hashed_password = get_password_hash(user_data.password)
    
    # Kullanıcı oluştur
    db_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        tc_identity_no=user_data.tc_identity_no,
        phone=user_data.phone,
        role=user_data.role,
        expertise_area=user_data.expertise_area,
        organization=user_data.organization,
        city=user_data.city,
        district=user_data.district,
        profile_photo_url=user_data.profile_photo_url
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # JWT token oluştur
    access_token = create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


@router.post("/login", response_model=schemas.AuthResponse)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # Kullanıcıyı bul
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı"
        )
    
    # Şifre kontrolü
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı"
        )
    
    # Aktif kullanıcı kontrolü
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı bırakılmış"
        )
    
    # JWT token oluştur
    access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


@router.put("/me", response_model=schemas.UserResponse)
def update_current_user(
    user_data: schemas.UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Token doğrulama
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Kullanıcıyı bul
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    # Sadece gönderilen alanları güncelle
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user
