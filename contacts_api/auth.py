import asyncio
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
from contacts_api.schemas import UserCreate, UserResponse, Token, ForgotPasswordSchema, ResetPasswordSchema
from contacts_api.utils import hash_password, verify_password
from contacts_api.email_utils import send_email
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis
import json

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

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_data = asyncio.run(redis_client.get(email))
        if user_data:
            return User(**json.loads(user_data))

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        asyncio.run(redis_client.setex(user.email, ACCESS_TOKEN_EXPIRE_MINUTES * 60, json.dumps({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
        })))
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_reset_token(email: str) -> str:
    to_encode = {"sub": email}
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@auth_router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordSchema, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = create_access_token({"sub": user.email})
    reset_link = f"http://127.0.0.1:8000/auth/reset-password?token={reset_token}"

    await send_email(
        "Сброс пароля",
        user.email,
        f"<h1>Сброс пароля</h1><p>Для сброса пароля перейдите по ссылке:</p><a href='{reset_link}'>Сбросить пароль</a>",
    )

    return {"message": "Password reset link sent to your email"}



@auth_router.post("/reset-password")
async def reset_password(payload: ResetPasswordSchema, db: Session = Depends(get_db)) -> dict:
    try:
        payload_data = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload_data.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(payload.new_password)
    db.commit()

    await redis_client.delete(email)
    return {"message": "Password has been reset successfully"}

@auth_router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> dict:
    result = upload(file.file)
    url, _ = cloudinary_url(result["public_id"], format="jpg")
    return {"avatar_url": url}