from sqlalchemy.orm import Session
import os
from . import models, schemas
from fastapi import UploadFile
import datetime

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()



def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def modify_user(db: Session, user: schemas.User):
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    db_user.email = user.email
    db_user.password = user.password
    db_user.is_active = user.is_active
    db_user.items = user.items
    db.commit()
    db.refresh(db_user)
    return db_user



def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int, origin_img_path: str, origin_img_size: int):
    db_item = models.Item(**item.dict(), owner_id=user_id, origin_img_path=origin_img_path, origin_img_size=origin_img_size)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


async def save_uploaded_image(file: UploadFile, user_id: int):
    upload_dir = f"uploads/user_{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return file_path, len(content)