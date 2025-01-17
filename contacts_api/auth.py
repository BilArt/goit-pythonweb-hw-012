from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from decouple import config
from sqlalchemy.orm import Session
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
import cloudinary
from contacts_api.database import get_db
from contacts_api.models import User
from contacts_api.schemas import UserCreate, UserResponse, Token
from contacts_api.utils import hash_password, verify_password
from contacts_api.email_utils import send_email
from datetime import datetime, timedelta
import redis.asyncio as redis
import uuid

cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET")
)

SECRET_KEY = config("SECRET_KEY", default="supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 10

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user_data = await redis_client.get(email)
    if user_data:
        return User(**eval(user_data))

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    await redis_client.setex(email, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(user.__dict__))
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_reset_token(email: str) -> str:
    to_encode = {"sub": email}
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        is_verified=False
    )
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
def login_user(user: UserCreate, db: Session = Depends(get_db)) -> Token:
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": db_user.email})
    redis_client.setex(db_user.email, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(db_user.__dict__))
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/verify-email")
def verify_email(email: str, db: Session = Depends(get_db)) -> dict:
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
) -> UserResponse:
    try:
        upload_result = upload(
            file.file,
            folder="user_avatars",
            public_id=f"avatar_{current_user.id}",
            overwrite=True
        )
        avatar_url, _ = cloudinary_url(upload_result["public_id"], format="jpg")

        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)

        redis_client.setex(current_user.email, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(current_user.__dict__))

        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")

@auth_router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = create_reset_token(email)
    reset_link = f"http://127.0.0.1:8000/auth/reset-password?token={reset_token}"
    email_body = f"""
    <h1>Сброс пароля</h1>
    <p>Для сброса пароля перейдите по ссылке:</p>
    <a href="{reset_link}">Сбросить пароль</a>
    """
    await send_email("Сброс пароля", email, email_body)
    return {"message": "Password reset link sent to your email"}

@auth_router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(new_password)
    db.commit()

    redis_client.delete(email)
    return {"message": "Password has been reset successfully"}
