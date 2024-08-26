import os
import ffmpeg
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from .models import Video
import shutil
import boto3

logger = get_task_logger(__name__)


@shared_task
def process_video(video_uuid, video_path):
    logger.info("Start getting the video object from uuid")

    environment = settings.ENVIRONMENT
    s3_client = boto3.client('s3')

    video = Video.objects.get(uuid=video_uuid)

    logger.info("Start creating the folder for chunk files for the video")

    # Path to store the video segments and mpd file
    segments_path = os.path.join(settings.MEDIA_ROOT, 'stream_video', 'chunks', str(video_uuid), 'segments')
    mpd_path = os.path.join(segments_path, 'manifest.mpd')

    # Create folder to store segments
    os.makedirs(segments_path, exist_ok=True)

    logger.info("Start generating the chunk files for the video")

    # Command to split video into segments and create mpd file audio
    try:
        (
            ffmpeg
            .input(video_path)
            .output(mpd_path,
                    format='dash',
                    map='0',
                    video_bitrate='2400k',
                    video_size='1920x1080',
                    vcodec='libx264',
                    seg_duration='4',  # Sets segment duration to 4 seconds
                    acodec='copy')
            .run()
        )
    except ffmpeg.Error as e:
        logger.error(e)
        print('Error occurred: ', e, flush=True)

    logger.info("Successfully generated the video segment files")

    if environment == "production":
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # Upload the segments and mpd file to S3
        for root, dirs, files in os.walk(segments_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_key = os.path.join('media', 'stream_video', 'chunks', str(video_uuid), 'segments', file)
                s3_client.upload_file(local_file_path, bucket_name, s3_key)
                logger.info(f"Uploaded {file} to S3")

        # Update the video object with the mpd file URL
        video.mpd_file_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(video_uuid), 'segments',
                                          'manifest.mpd')
        video.save()

        # Clean up the local segment files
        segments_parent_directory = os.path.dirname(segments_path)
        shutil.rmtree(segments_parent_directory, ignore_errors=True)
        logger.info("Deleted local segment files and parent directory")

    else:
        # Update the video object with the mpd file URL
        video.mpd_file_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(video_uuid), 'segments',
                                          'manifest.mpd')
        video.save()

    # Clean up the temporary video file
    os.remove(video_path)
    logger.info("Deleted the video file permanently")

    # Remove the parent directory of the video file
    parent_directory = os.path.dirname(video_path)
    shutil.rmtree(parent_directory, ignore_errors=True)
    logger.info("Deleted the video parent directory")

    return "Task Successful"
