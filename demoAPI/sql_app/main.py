from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, items
from .redis_utils import redis_client
from redis.exceptions import RedisError
from . import models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="图片矫正系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, tags=["认证"])
app.include_router(users.router, tags=["用户"])
app.include_router(items.router, tags=["项目"])


@app.on_event("startup")
async def startup_event():
    try:
        redis_client.ping()
        print("Successfully connected to Redis")
    except RedisError:
        print("Failed to connect to Redis")


@app.get("/")
async def main():
    return {"message": "Welcome to the Image Correction System"}
