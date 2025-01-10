#!/bin/sh

# wait for redis server to start
sleep 10

celery -A video_streaming_backend worker --concurrency=1 --queues=high_priority,medium_priority,low_priority --loglevel=info