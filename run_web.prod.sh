#!/bin/sh

su -m root -c "python manage.py migrate"
su -m root -c "gunicorn video_streaming_backend.wsgi:application --bind 0.0.0.0:8000"