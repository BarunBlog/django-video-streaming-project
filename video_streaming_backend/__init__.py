# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "video_streaming_backend.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# order of the import matters here
from .celery import app as celery_app

__all__ = ('celery_app',)
