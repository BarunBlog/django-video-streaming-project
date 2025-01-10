import os
from celery import Celery
from django.conf import settings

# set settings for celery cmd program
os.environ.setdefault('DJANGO-SETTINGS-MODULE', 'video_streaming_backend.settings')

app = Celery('video_streaming_backend', broker=settings.CELERY_BROKER_URL)

# Define queues and default queue
app.conf.task_queues = {
    "high_priority": {"exchange": "high_priority", "routing_key": "high_priority"},
    "medium_priority": {"exchange": "medium_priority", "routing_key": "medium_priority"},
    "low_priority": {"exchange": "low_priority", "routing_key": "low_priority"},
}

app.conf.task_default_queue = "medium_priority"

app.conf.task_routes = {
    "setup_and_process_video": {"queue": "high_priority"},
    "extract_video_metadata": {"queue": "high_priority"},
    "upload_segments_to_s3": {"queue": "medium_priority"},
    "save_segments_to_db": {"queue": "low_priority"},
    "cleanup_files": {"queue": "low_priority"},
    "update_last_streamed_segment": {"queue": "high_priority"},
}

# automatically discover tasks given in different apps
app.autodiscover_tasks(settings.INSTALLED_APPS)

app.conf.update(
    result_backend='django-db',
)
