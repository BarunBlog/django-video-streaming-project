import redis
from django.conf import settings

# # Redis client configuration
# redis_client = redis.StrictRedis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=settings.REDIS_DB,
#     decode_responses=True  # Automatically decode byte strings to strings
# )
#
# redis_client_without_decoded_response = redis.StrictRedis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=settings.REDIS_DB,
#     decode_responses=False
# )

# Redis cluster client configuration
redis_client = redis.RedisCluster(
    host=settings.REDIS_CLUSTER_NODES,
    decode_responses=True  # Automatically decode byte strings to strings
)

redis_client_without_decoded_response = redis.RedisCluster(
    host=settings.REDIS_CLUSTER_NODES,
    decode_responses=False
)
