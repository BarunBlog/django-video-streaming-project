FROM python:3.10

# Install FFmpeg and other necessary packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    make

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["make", "migrate_and_runserver"]