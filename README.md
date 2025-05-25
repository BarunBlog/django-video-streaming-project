# Video-Streaming-System

This is the completed backend component of the video streaming application built with Django.

## Technology used

Python, Django, Django Rest Framework, Celery, Redis, Redis Cluster, Flower, Postgresql and Docker.

# Prerequisites

1. To run this project, you need to install docker on your system.
2. You must need to create s3 bucket before running this project.
3. The AWS infra setup is given in this
   repository [video streaming infra](https://github.com/BarunBlog/video-streaming-infra)

# Installation

1. Clone the repository:
2. Change directory to django-video-streaming-project by running `cd django-video-streaming-project`
3. Set up the following environment variables:
4. I provided environment for both local and production environment.

#### .env for local development:

```
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=SRGTSZ25GUAY43ahfv@1zd6f8g435sfg65GsduGF*%^76bjgzsdg

DB_NAME=videostream_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=dev-db # host ip in production
DB_PORT=5432

REDIS_HOST=redis # host ip in production
REDIS_PORT=6379
REDIS_DB=0

AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
AWS_STORAGE_BUCKET_NAME=vidizone-streamer1
AWS_S3_REGION_NAME=ap-southeast-1


FLOWER_BASIC_AUTH=BarunAdmin:BarunAdmin@1234


```

##### Note:

If you want to run in production mode, then you need to include the bellow part to .env file

```
NFS_STORAGE_HOST=<nfs_server_private_ip>

REDIS_CLUSTER_HOST1=<cluster_node1_private_ip>
REDIS_CLUSTER_HOST2=<cluster_node2_private_ip>
REDIS_CLUSTER_HOST3=<cluster_node3_private_ip>
REDIS_CLUSTER_HOST4=<cluster_node4_private_ip>
REDIS_CLUSTER_HOST5=<cluster_node5_private_ip>
REDIS_CLUSTER_HOST6=<cluster_node6_private_ip>
REDIS_CLUSTER_PORT=6379

SSH_APP_HOST1=<app_server_1_private_ip>
SSH_APP_HOST2=<app_server_2_private_ip>

SSH_BASTION_HOST=<nginx_server_public_ip>

SSH_FLOWER_HOST=<flower_server_private_ip>

SSH_PRIVATE_KEY=<aws_private_key_pair>
SSH_USER=ubuntu

SSH_WORKER_HOST1=<worker_server1_private_ip>
SSH_WORKER_HOST2=<worker_server2_private_ip>
```

Create a .env file in the root directory and provide the required values for environment variables such as database
credentials.

# Build Docker containers:

To run this project, you just need to run the following command and the rest will do itself.

```docker compose -f compose.web.yml up```

This command will build and start the Docker containers required for the project.

### Task monitoring with flower

To monitor the task, you need to run another command
```docker compose -f compose.flower.yml up```

# Admin Interface:

The admin panel can be accessed at http://localhost/admin/,
But you need to create a superuser account first.

# Create Superuser Account

To visit the admin interface, you need to create a superuser account from the docker cli

```docker exec -it video-streaming-backend python manage.py createsuperuser```