from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

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
