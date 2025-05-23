import redis
from django.conf import settings

Environment = settings.ENVIRONMENT

if Environment == "development":
    # # Redis client configuration
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True  # Automatically decode byte strings to strings
    )

    redis_client_without_decoded_response = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=False
    )
    
elif Environment == "production":
    # Redis cluster client configuration
    redis_client = redis.RedisCluster(
        startup_nodes=settings.REDIS_CLUSTER_NODES,
        decode_responses=True  # Automatically decode byte strings to strings
    )

    redis_client_without_decoded_response = redis.RedisCluster(
        startup_nodes=settings.REDIS_CLUSTER_NODES,
        decode_responses=False
    )
