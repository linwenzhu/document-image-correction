from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class ItemBase(BaseModel):
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    origin_img_path: Optional[str]
    correction_img_path: Optional[str]
    upload_time: datetime
    owner_id: int
    origin_img_size: Optional[int]
    correction_img_size: Optional[int]

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str



class User(UserBase):
    id: int
    email: EmailStr
    register_time: datetime = None
    last_updated: datetime = None
    is_active: bool
    items: list[Item] = []
    role: UserRole

    class Config:
        orm_mode = True
        from_attributes = True


class TokenData(BaseModel):
    username: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class EmailSchema(BaseModel):
    email: EmailStr


class LoginData(BaseModel):
    username_or_email: str
    password: str


class EmailVerification(BaseModel):
    email: EmailStr
    verification_code: str


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
