from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: Optional[date]
    additional_info: Optional[str]


class ContactResponse(ContactCreate):
    id: int

    class Config:
        orm_mode = True


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
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
