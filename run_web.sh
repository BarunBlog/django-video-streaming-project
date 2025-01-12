#!/bin/sh

su -m root -c "python manage.py migrate"
#su -m root -c "python manage.py collectstatic --noinput"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in production mode"
    su -m root -c "gunicorn --workers=4 --worker-class=gevent --bind 0.0.0.0:8000 video_streaming_backend.wsgi"
else
    echo "Running in development mode"
    su -m root -c "python manage.py runserver 0.0.0.0:8000"
fi
