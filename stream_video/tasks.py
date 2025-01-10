import os
import ffmpeg
from botocore.exceptions import NoCredentialsError, BotoCoreError
from video_streaming_backend.celery import app
from celery import states, chain
from celery.utils.log import get_task_logger
from celery.exceptions import Retry, Ignore, MaxRetriesExceededError
from django.conf import settings
from django.db import DatabaseError
from .models import Video, VideoSegment
from . import models
import shutil
import boto3

logger = get_task_logger(__name__)


@app.task(bind=True, name="setup_and_generate_segments")
def setup_and_generate_segments(self, video_uuid, video_path):
    logger.info("Start creating the folder for chunk files for the video")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    segments_path = os.path.join(settings.MEDIA_ROOT, 'stream_video', 'chunks', str(video_uuid), 'segments')
    os.makedirs(segments_path, exist_ok=True)

    logger.info("Generating segments and MPD file.")

    mpd_path = os.path.join(segments_path, 'manifest.mpd')

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
                    seg_duration='4',
                    acodec='copy')
            .run()
        )
    except ffmpeg.Error as e:
        error_message = f"Error during segment generation: {e}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})
        raise Ignore()

    logger.info("Successfully generated the video segment files")
    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})

    return {
        "video_uuid": video_uuid,
        "video_path": video_path,
        "segments_path": segments_path,
    }


@app.task(bind=True, name="extract_video_metadata")
def extract_video_metadata(self, setup_data):
    logger.info("Extracting video metadata.")
    video_path = setup_data["video_path"]

    try:
        metadata = ffmpeg.probe(video_path)
        duration = float(metadata['format']['duration'])
        setup_data["duration"] = duration
        logger.info(f"Video duration: {duration} seconds.")
    except ffmpeg.Error as e:
        logger.error(f"Error extracting metadata: {e}")
        setup_data["duration"] = 0

    return setup_data


@app.task(bind=True, name="upload_segments_to_s3", max_retries=2)
def upload_segments_to_s3(self, setup_data):
    if settings.ENVIRONMENT == "production":
        logger.info("Uploading segments to S3.")

        self.update_state(state=states.STARTED, meta={"status": "Processing"})

        s3_client = boto3.client('s3')
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        segments_path = setup_data["segments_path"]
        video_uuid = setup_data["video_uuid"]

        for root, dirs, files in os.walk(segments_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_key = os.path.join('media', 'stream_video', 'chunks', str(video_uuid), 'segments', file)

                try:
                    logger.info(f"Uploading {file} to S3...")
                    s3_client.upload_file(local_file_path, bucket_name, s3_key)
                    logger.info(f"Uploaded {file} successfully.")
                except (BotoCoreError, NoCredentialsError) as e:
                    logger.error(f"Error uploading {file} to S3: {e}")

                    # Retry the task
                    try:
                        raise self.retry(
                            countdown=5,  # Retry after 5 seconds
                            exc=e,
                            max_retries=self.max_retries  # Maximum retries
                        )
                    except MaxRetriesExceededError:
                        logger.error(f"Maximum retries exceeded for {file}.")
                        self.update_state(
                            state=states.FAILURE,
                            meta={"status": f"Failed to upload {file} after {self.max_retries} retries."}
                        )
                        raise Retry(f"Max retries reached for {file}.")

    return setup_data


@app.task(bind=True, name="save_segments_to_db")
def save_segments_to_db(self, setup_data):
    logger.info("Saving segments data to database.")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    video = Video.objects.get(uuid=setup_data["video_uuid"])
    segments_path = setup_data["segments_path"]
    video_uuid = setup_data["video_uuid"]

    for root, dirs, files in os.walk(segments_path):
        for file in files:
            segment_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(video_uuid), 'segments', file)
            VideoSegment.objects.create(video=video, segment_name=file, segment_url=segment_url)

    video.mpd_file_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(video_uuid), 'segments',
                                      'manifest.mpd')
    video.duration = setup_data.get("duration", 0)
    video.save()

    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})

    return setup_data


@app.task(bind=True, name="cleanup_files")
def cleanup_files(self, setup_data):
    logger.info("Cleaning up temporary files.")
    video_path = setup_data["video_path"]
    segments_parent_path = os.path.join(settings.MEDIA_ROOT, 'stream_video', 'chunks', str(setup_data["video_uuid"]))
    environment = settings.ENVIRONMENT

    if environment == "production":
        shutil.rmtree(os.path.dirname(segments_parent_path), ignore_errors=True)
        logger.info("Deleted the video segment files")

    # Clean up the temporary video file
    os.remove(video_path)

    # Remove the parent directory of the video file
    parent_directory = os.path.dirname(video_path)
    shutil.rmtree(parent_directory, ignore_errors=True)

    logger.info("Deleted the video and parent directory")

    return "Task Successful"


def process_video(video_uuid: str, video_path: str):
    # Define the chain
    video_processing_chain = chain(
        setup_and_generate_segments.s(video_uuid, video_path),
        extract_video_metadata.s(),
        upload_segments_to_s3.s(),
        save_segments_to_db.s(),
        cleanup_files.s()
    )

    # Start the chain of tasks, no need to pass args here
    video_processing_chain.apply_async()


@app.task(bind=True, name="update_last_streamed_point", max_retries=1)
def update_last_streamed_segment(self, user_id: int, video_uuid: str, last_played_second: int):
    logger.info("Start updating the last streamed point")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    # Get video by video_uuid
    try:
        video: Video = models.get_video_by_uuid(video_uuid=video_uuid)
    except Video.DoesNotExist as e:
        error_message = "Video not found with the given UUID."
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})
        raise Ignore()  # Skip further processing

    # Update or create the last streamed segment
    try:
        models.save_last_streamed_point(user_id=user_id, video=video, last_played_second=last_played_second)
    except DatabaseError as e:
        error_message = f"Database error while updating last streamed segment: {e}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})

        # Retry only for transient database issues
        retry_in = 10
        logger.info(f"Retrying in {retry_in} seconds...")
        raise self.retry(exc=e, countdown=retry_in)

    # Task completed successfully
    logger.info("Last streamed point updated successfully.")
    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})
    return {"status": "Completed", "user_id": user_id, "video_uuid": video_uuid}
