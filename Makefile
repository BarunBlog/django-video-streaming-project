docker-build:
	docker compose up --build

docker-down:
	docker compose down

docker-start: |
	docker-down docker-build

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