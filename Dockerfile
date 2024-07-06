FROM python:3.10-alpine

# Install FFmpeg and other necessary packages
RUN apk update && apk add --no-cache \
    ffmpeg \
    make \
    build-base

EXPOSE 8000
WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

COPY run_web.sh /run_web.sh
COPY run_celery.sh /run_celery.sh

RUN chmod +x /run_web.sh
RUN chmod +x /run_celery.sh