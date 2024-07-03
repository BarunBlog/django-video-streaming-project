#!/bin/sh

su -m root -c "python manage.py migrate"
su -m root -c "python manage.py runserver 0.0.0.0:8000"