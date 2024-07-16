from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库设置
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # 邮件服务器设置
    MAIL_USERNAME: str= "1904285808@qq.com"
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str

    # JWT设置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
