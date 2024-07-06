#!/bin/sh

# wait for RabbitMQ server to start
sleep 10

celery -A video_streaming_backend worker --loglevel=info