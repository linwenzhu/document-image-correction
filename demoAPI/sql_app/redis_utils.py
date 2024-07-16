import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)


def set_user_session(user_id: int, token: str, expire_time: int):
    redis_client.setex(f"user_session:{user_id}", expire_time, token)


def get_user_session(user_id: int):
    return redis_client.get(f"user_session:{user_id}")


def delete_user_session(user_id: int):
    redis_client.delete(f"user_session:{user_id}")


def is_token_valid(user_id: int, token: str):
    stored_token = redis_client.get(f"user_session:{user_id}")
    return stored_token and stored_token.decode() == token
