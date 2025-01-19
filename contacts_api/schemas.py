from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class ContactResponse(ContactCreate):
    id: int

    class Config:
        model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_verified: bool

    class Config:
        model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str
