from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from decouple import config
from sqlalchemy.orm import Session
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.utils import cloudinary_url
from contacts_api.database import get_db
from contacts_api.models import User
from contacts_api.schemas import UserCreate, UserResponse, Token
from contacts_api.utils import hash_password, verify_password
from contacts_api.email_utils import send_email
from datetime import datetime, timedelta

SECRET_KEY = config("SECRET_KEY", default="supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter()

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, password=hashed_password, full_name=user.full_name, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    verification_link = f"http://127.0.0.1:8000/auth/verify-email?email={new_user.email}"
    email_body = f"""
    <h1>Подтверждение email</h1>
    <p>Для подтверждения вашего аккаунта перейдите по ссылке:</p>
    <a href="{verification_link}">Подтвердить Email</a>
    """
    await send_email("Подтверждение Email", new_user.email, email_body)

    return new_user


@auth_router.post("/login", response_model=Token)
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@auth_router.get("/verify-email")
def verify_email(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()
    return {"message": "Email successfully verified"}


@auth_router.post("/upload-avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        upload_result = cloudinary_upload(
            file.file,
            folder="user_avatars",
            public_id=f"avatar_{current_user.id}",
            overwrite=True
        )
        avatar_url, _ = cloudinary_url(upload_result["public_id"], format="jpg")

        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)

        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")