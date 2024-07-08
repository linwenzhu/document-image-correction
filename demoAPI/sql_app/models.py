from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship,sessionmaker
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True,index=True,unique=True)
    username = Column(String)
    password = Column(String)
    register_time = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    is_active = Column(Boolean, default=True)


    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)

    origin_img_path =Column(String)
    correction_img_path = Column(String)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    origin_img_size = Column(Integer)
    correction_img_size = Column(Integer)


    owner = relationship("User", back_populates="items")


