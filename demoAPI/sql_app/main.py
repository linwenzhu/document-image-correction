from fastapi import Depends, FastAPI, HTTPException, UploadFile, status, Query, Body, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from . import crud, models, schemas, image_processor
from .database import SessionLocal, engine
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import Optional, List

from jose import JWTError, jwt
import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi.responses import FileResponse
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="图片矫正系统")

# 配置日志
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
log_file = 'app.log'
my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 跨域
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # 允许所有域名
   allow_credentials=True,
   allow_methods=["*"],  # 允许所有方法
   allow_headers=["*"],  # 允许所有头
)

SECRET_KEY = "your-secret-key" #待修改
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user==None:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=schemas.Token,tags=["已实现"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.post("/register", tags=["已实现"], response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 创建新用户
    new_user = crud.create_user(db=db, user=user)

    # 返回用户信息，但不包括密码
    return schemas.User.from_orm(new_user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.put("/users/{user_id}", response_model=schemas.User)
def update_users(user_id:int, newuser:schemas.User,skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.modify_user(db, newuser)
    return users



@app.get("/users/{user_id}/item_ids",tags=["已实现"], response_model=List[int])
def read_user_item_ids(user_id: int, db: Session = Depends(get_db)):
    item_ids = crud.get_user_item_ids(db, user_id=user_id)
    if not item_ids:
        raise HTTPException(status_code=404, detail="No items found for this user")
    return item_ids

@app.post("/users/{user_id}/items/", response_model=schemas.Item, tags=["已实现"])
async def create_item_for_user(
        user_id: int,
        description: str = Form(None),
        file: UploadFile = UploadFile(...),
        db: Session = Depends(get_db)
):


    try:
        # 创建 ItemCreate 对象
        item = schemas.ItemCreate(description=description)

        # 创建 item
        db_item = crud.create_user_item(db=db, item=item, user_id=user_id)


        # 保存图片
        file_path, file_size = await crud.save_uploaded_image(file, db_item.id)

        # 更新 item 的图片路径和大小
        db_item.origin_img_path = file_path
        db_item.origin_img_size = file_size
        db.commit()
        db.refresh(db_item)

        return db_item
    except Exception as e:
        app_log.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Error processing request: {str(e)}")

@app.post("/process/{item_id}/",response_model=schemas.Item,tags=["已实现"])
def process_image(item_id: int, db:Session = Depends(get_db)):
    db_item = crud.get_item(db,item_id= item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    image_path = db_item.origin_img_path

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        # 处理图像
        result = image_processor.process_image(image_path)
        processed_image_path = result
        processed_image_size = os.path.getsize(processed_image_path)
        print(result)
        updated_item = crud.update_item_image_info(db, item_id, processed_image_path, processed_image_size)
        return updated_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/{item_id}/{image_type}",tags=["已实现"])
async def get_image(item_id: int, image_type: str, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if image_type == "original":
        image_path = db_item.origin_img_path
    elif image_type == "corrected":
        image_path = db_item.correction_img_path
    else:
        raise HTTPException(status_code=400, detail="Invalid image type")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(image_path)



@app.get("/")
async def main():
    return {"message": "Hello World"}