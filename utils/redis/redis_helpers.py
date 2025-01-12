from utils.redis.redis_config import redis_client
from django.conf import settings


def cache_presigned_urls(video_uuid: str, presigned_urls: dict, ttl: int = settings.PRESIGNED_URL_EXPIRY_TIME):
    """
    Store presigned URLs for a video in Redis
    """

    redis_key = f"presigned_urls:{video_uuid}"
    redis_client.hmset(redis_key, presigned_urls)
    redis_client.expire(redis_key, ttl)


def get_presigned_urls(video_uuid: str) -> dict:
    """
    Fetch presigned URLs for a video from Redis.
    """
    redis_key = f"presigned_urls:{video_uuid}"
    return redis_client.hgetall(redis_key)
