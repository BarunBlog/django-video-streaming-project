DOCKER_USERNAME = barun25

APP_SERVER_IMAGE_NAME = django_video_streaming_app_server
APP_SERVER_TAG = latest
APP_SERVER_IMAGE = $(DOCKER_USERNAME)/$(APP_SERVER_IMAGE_NAME):$(APP_SERVER_TAG)
COMPOSE_WEB_FILE = compose.web.prod.yml

WORKER_SERVER_IMAGE_NAME = celery_video_streaming_worker_server
WORKER_SERVER_TAG = latest
WORKER_SERVER_IMAGE = $(DOCKER_USERNAME)/$(WORKER_SERVER_IMAGE_NAME):$(WORKER_SERVER_TAG)
COMPOSE_WORKER_FILE = compose.worker.prod.yml

# App Server
build-app-server:
	docker compose -f $(COMPOSE_WEB_FILE) build

tag-app-server:
	docker tag $(APP_SERVER_IMAGE_NAME):$(APP_SERVER_TAG) $(APP_SERVER_IMAGE)

push-app-server:
	docker push $(APP_SERVER_IMAGE)

all-app-server: build-app-server tag-app-server push-app-server

run-app-server:
	docker compose -f $(COMPOSE_WEB_FILE) up

# Worker Server
build-worker-server:
	docker compose -f $(COMPOSE_WORKER_FILE) build

tag-worker-server:
	docker tag $(WORKER_SERVER_IMAGE_NAME):$(WORKER_SERVER_TAG) $(WORKER_SERVER_IMAGE)

push-worker-server:
	docker push $(WORKER_SERVER_IMAGE)

all-worker-server: build-worker-server tag-worker-server push-worker-server

run-worker-server:
	docker compose -f $(COMPOSE_WORKER_FILE) up



docker-build:
	docker compose up --build

docker-down:
	docker compose down

docker-start: |
	docker-down docker-build

compose-up: |
	docker compose up --build --remove-orphans
	docker image prune --force

compose-prod-up: |
	docker compose -f docker-compose.prod.yml up --build --remove-orphans
	docker image prune --force

docker-clean:
	docker system prune -f # Remove unused cache, data, images

runserver: |
	python manage.py runserver 0.0.0.0:8000

migrate_and_runserver: |
	python manage.py migrate
	python manage.py runserver 0.0.0.0:8000

generate_video_segments:
	mkdir -p ./stream_video/static/stream_video/segments
	ffmpeg -i ./stream_video/static/stream_video/videos/nature_video.mp4 -map 0 -b:v 2400k -s:v 1920x1080 -c:v libx264 -an -f dash ./stream_video/static/stream_video/segments/nature_video.mpd

generate_video_segments_with_sound: |
	mkdir -p ./stream_video/static/stream_video/segments
	ffmpeg -i ./stream_video/static/stream_video/videos/nature_video.mp4 -map 0 -b:v 2400k -s:v 1920x1080 -c:v libx264 -acodec copy -f dash ./stream_video/static/stream_video/segments/nature_video.mpd


generate-ssh-key:
	ssh-keygen -t rsa -b 4096 -f ~/.ssh/github

modify-ec2-auth-keys:
	sudo nano ~/.ssh/authorized_keys

