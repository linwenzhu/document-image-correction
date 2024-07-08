from fastapi import Depends, FastAPI, HTTPException, UploadFile, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from . import crud, models, schemas
from .database import SessionLocal, engine
from fastapi.responses import HTMLResponse
import os


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="图片矫正系统")


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



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    dbuser = crud.get_user_by_email(db, token)
    if not dbuser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return dbuser


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user==None:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token",tags=["登录"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    dbuser = crud.get_user_by_email(db, form_data.username)
    if not dbuser:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    fpwd=form_data.password
    if not fpwd == dbuser.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": dbuser.email, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.put("/users/{user_id}", response_model=schemas.User)
def update_users(user_id:int, newuser:schemas.User,skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.modify_user(db, newuser)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
    user_id: int,
    item: schemas.ItemCreate,
    file: UploadFile = UploadFile(...),
    db: Session = Depends(get_db)
):
    file_path, file_size = await crud.save_uploaded_image(file, user_id)
    return crud.create_user_item(db=db, item=item, user_id=user_id, origin_img_path=file_path, origin_img_size=file_size)

@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

#@app.post("/uploadfile/")
#async def create_upload_file(file: UploadFile):
#    return {"filename": file.filename}



@app.get("/")



@app.get("/")
async def main():
    content = """
<body>
<form action="/uploadfile/" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
   """
    return HTMLResponse(content=content)
