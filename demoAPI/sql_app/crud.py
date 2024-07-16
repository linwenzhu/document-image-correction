import random
import string

from sqlalchemy.orm import Session
import os
import secrets
from . import models, schemas
from fastapi import UploadFile
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_password_reset_token(db: Session, email: str):
    user = get_user_by_email(db, email)
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.commit()
        return token
    return None


def reset_password(db: Session, token: str, new_password: str):
    user = db.query(models.User).filter(models.User.reset_token == token).first()
    if user and user.reset_token_expires > datetime.utcnow():
        user.password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        return True
    return False


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        username=user.username,
        role=models.UserRole.USER  # 默认设置为普通用户
    )
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


def create_verification_code(db: Session, user_id: int):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    # 检查是否已存在该用户的验证码
    existing_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == user_id
    ).first()

    if existing_code:
        # 如果存在，更新现有记录
        existing_code.code = code
        existing_code.expires_at = expires_at
        db_code = existing_code
    else:
        # 如果不存在，创建新记录
        db_code = models.VerificationCode(code=code, user_id=user_id, expires_at=expires_at)
        db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return db_code.code


def verify_code(db: Session, user_id: int, code: str):
    db_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == user_id,
        models.VerificationCode.code == code,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if db_code:
        # 验证成功后，删除已使用的验证码
        db.delete(db_code)
        db.commit()
        return True
    return False




def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def update_user(db: Session, db_user: models.User, user: schemas.UserUpdate):
    for var, value in vars(user).items():
        if value is not None:
            setattr(db_user, var, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


