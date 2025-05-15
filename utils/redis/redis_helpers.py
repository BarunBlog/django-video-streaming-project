import json
from utils.redis.redis_config import redis_client
from django.conf import settings


def cache_presigned_urls(video_uuid: str, presigned_urls: dict, ttl: int = settings.PRESIGNED_URL_EXPIRY_TIME):
    """
    Store presigned URLs for a video in Redis
    """

    redis_key = f"presigned_urls:{video_uuid}"

    # Serialize nested dict values to JSON strings
    serialized_mapping = {
        key: json.dumps(value) for key, value in presigned_urls.items()
    }

    redis_client.hset(redis_key, mapping=serialized_mapping)
    redis_client.expire(redis_key, ttl)


def get_presigned_urls(video_uuid: str) -> dict:
    """
    Fetch presigned URLs for a video from Redis.
    """
    redis_key = f"presigned_urls:{video_uuid}"

    raw_data = redis_client.hgetall(redis_key)

    # Deserialize JSON string back to nested dict
    presigned_urls = {
        key: json.loads(value) for key, value in raw_data.items()
    }

    return presigned_urls


def increment_segment_activity(video_uuid: str, segment_names: list[str]):
    redis_key = f"segment_activity:{video_uuid}"

    """
    A Redis pipeline allows multiple commands to be queued and executed together in a batch,
    reducing network round-trips.
    """
    pipe = redis_client.pipeline()
    for segment in segment_names:
        pipe.hincrby(redis_key, segment, 1)

    pipe.expire(redis_key, settings.SEGMENT_ACTIVITY_EXPIRY)
    pipe.execute()
