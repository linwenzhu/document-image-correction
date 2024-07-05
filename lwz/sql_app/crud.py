from sqlalchemy.orm import Session

from . import models, schemas
import os
from fastapi import UploadFile


async def save_uploaded_image(file: UploadFile, user_id: int):
    # 创建上传目录（如果不存在）
    upload_dir = f"uploads/user_{user_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一的文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{user_id}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return file_path

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, password=user.password)
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


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def images(db:Session):
    return db.query(models.Aimage) .all()

