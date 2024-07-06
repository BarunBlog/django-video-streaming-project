import os
import ffmpeg
from celery import shared_task
from django_celery_results.models import TaskResult
from celery.utils.log import get_task_logger
from django.conf import settings
from .models import Video

logger = get_task_logger(__name__)


@shared_task
def process_video(video_uuid, video_path):
    logger.info("Start getting the video object from uuid")

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
                    acodec='aac')
            .run()
        )
    except ffmpeg.Error as e:
        logger.error(e)
        print('Error occurred: ', e, flush=True)

    logger.info("Successfully generated the video segment files")

    # Update the video object with the mpd file URL
    video.mpd_file_url = mpd_path
    video.save()

    # Clean up the temporary video file
    os.remove(video_path)

    return "Task Successful"



