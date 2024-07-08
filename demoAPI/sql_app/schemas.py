from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    title: str
    description: str | None = None


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
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    user_id: int
    register_time: datetime
    last_updated: datetime
    is_active: bool
    items: list[Item] = []

    class Config:
        orm_mode = True

