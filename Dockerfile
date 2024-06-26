FROM python:3.10-alpine

# Install FFmpeg and other necessary packages
RUN apk update && apk add --no-cache \
    ffmpeg \
    make \
    build-base \
    linux-headers

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["make", "migrate_and_runserver"]