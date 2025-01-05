from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from contacts_api.database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    birthday = Column(String)
    additional_info = Column(String)
    user_id = Column(Integer, ForeignKey("users.id")) 
    user = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_verified = Column(Boolean, default=False)
    contacts = relationship("Contact", back_populates="user")
