# Video-Streaming-System

This is the completed backend component of the video streaming application built with Django.

## Technology used

Python, Django, Django Rest Framework, Celery, RabbitMQ, Postgresql and Docker.

# Prerequisites

1. To run this project you need to install docker on your system.

# Installation

1. Clone the repository:
2. Change directory to django-video-streaming-project by running `cd django-video-streaming-project`
3. Set up following environment variables:

```
ENVIRONMENT=production
DEBUG=True
SECRET_KEY=SRGTSZ25GUAY43ahfv@1zd6f8g435sfg65GsduGF*%^76bjgzsdg

DB_NAME=videostream_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=host.docker.internal
DB_PORT=5430


RABBITMQ_HOST=host.docker.internal
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_STORAGE_BUCKET_NAME=your_s3_bucket_name
AWS_S3_REGION_NAME=your_s3_region_name

```

Create a .env file in the root directory and provide the required values for environment variables such as database
credentials.

Note that if you want to run this locally then please change the variable to `ENVIRONMENT=development`. In that case you
don't need to configure the S3 bucket.

# Build Docker containers:

To run this project you just need to run the following command and the rest will do itself.

```make compose-up ```

This command will build and start the Docker containers required for the project.

# Collect Static files:

If you are in the `production` environment then you need to run the collect static command to work with django admin
panel.

`python manage.py collectstatic`

You need to run this command from the docker container `video-streaming-backend`

# Admin Interface:

The admin panel can be accessed at http://localhost:8000/admin/
But you need to create a superuser account first.

# Create Super User Account

To visit the admin interface you need to create a superuser account from the docker cli

``` docker exec -it video-streaming-backend python manage.py createsuperuser ```