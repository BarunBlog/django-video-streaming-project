import json

from stream_video.tasks import cache_popular_segment_file
from utils.redis.redis_config import redis_client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


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


def get_presigned_url(video_uuid: str, segment_name: str) -> dict:
    """
        Fetch presigned URL for a segment file from Redis.
    """
    presigned_url_key = f"presigned_urls:{video_uuid}"

    raw_data = redis_client.hget(presigned_url_key, segment_name)

    presigned_url = json.loads(raw_data)

    return presigned_url


def increment_segment_activity(video_uuid: str, segment_names: list[str]):
    """
    A Redis pipeline allows multiple commands to be queued and executed together in a batch,
    reducing network round-trips.
    """
    pipe = redis_client.pipeline()

    keys = []
    for segment in segment_names:
        key = f"segment_activity: {video_uuid}:{segment}"
        keys.append((segment, key))
        pipe.incr(key)
        pipe.expire(key, settings.SEGMENT_ACTIVITY_EXPIRY)

    results = pipe.execute()  # results = [count1, True, count2, True, count3, True, ...]
    logger.info(f"Updated the segment activity in redis")

    # Checking if segment popularity exceeded the threshold
    for i, (segment, key) in enumerate(keys):
        count = results[i * 2]
        if count == settings.SEGMENT_POPULARITY_THRESHOLD:
            segment_cached_flag = f"segment_cached_flag:{video_uuid}:{segment}"
            
            # Only set this key if it doesn't already exist
            if redis_client.set(segment_cached_flag, "1", nx=True, ex=settings.CACHED_SEGMENT_EXPIRY):
                logger.info(f"Caching the segment file {segment}")
                cache_popular_segment_file.delay(video_uuid, segment)
