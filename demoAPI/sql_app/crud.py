from sqlalchemy.orm import Session
import os
from . import models, schemas
from fastapi import UploadFile
import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()



def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)
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



def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


async def save_uploaded_image(file: UploadFile, item_id: int):
    # 使用 os.path.join 来创建路径，确保跨平台兼容性
    item_dir = os.path.join("uploads", f"item_{item_id}")
    origin_dir = os.path.join(item_dir, "origin")

    # 确保目录存在
    os.makedirs(origin_dir, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{item_id}_{file_extension}"

    file_path = os.path.join(origin_dir, unique_filename)

    # 使用 'with' 语句确保文件正确关闭
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 确保返回的路径使用正斜杠，并且各部分正确分隔
    return file_path.replace('\\', '/'), len(content)

def update_item_image_path(db: Session, item_id: int, correction_img_path: str):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db_item.correction_img_path = correction_img_path
        db.commit()
        db.refresh(db_item)
    return db_item

def update_item_image_info(db: Session, item_id: int, correction_img_path: str, correction_img_size: int):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db_item.correction_img_path = correction_img_path
        db_item.correction_img_size = correction_img_size
        db.commit()
        db.refresh(db_item)
    return db_item

def get_user_item_ids(db: Session, user_id: int):
    items = db.query(models.Item.id).filter(models.Item.owner_id == user_id).all()
    return [item.id for item in items]