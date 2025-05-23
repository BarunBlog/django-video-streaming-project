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
import subprocess
import requests
from utils.redis.redis_config import redis_client
import json

logger = get_task_logger(__name__)


@app.task(bind=True, name="setup_and_generate_segments", queue="high_priority")
def setup_and_process_video(self, video_uuid, video_path):
    logger.info("Checking if the video file is accessible from the worker")

    # Check if file exists
    if not os.path.exists(video_path):
        logger.error(f"Video file not found at {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Check if file is readable
    if not os.access(video_path, os.R_OK):
        logger.error(f"Permission denied: Cannot read video file at {video_path}")
        raise PermissionError(f"Permission denied: Cannot read video file at {video_path}")

    logger.info("Start creating the folder for chunk files for the video")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    base_storage_path = settings.MEDIA_ROOT + 'stream_video/chunks'

    segments_path = os.path.join(base_storage_path, str(video_uuid), 'segments')
    os.makedirs(segments_path, exist_ok=True)

    mpd_path = os.path.join(segments_path, 'manifest.mpd')

    logger.info("Generating multi-resolution DASH segments and MPD file")

    """
        init-stream0.m4s initialization segments for 480p
        init-stream1.m4s initialization segments for 720p
        init-stream2.m4s initialization segments for 1080p

        chunk-stream0-00001.m4s media segments (chunks) for 480p
        chunk-stream1-00001.m4s media segments (chunks) for 720p
        chunk-stream2-00001.m4s media segments (chunks) for 1080p
    """

    command = [
        'ffmpeg',
        '-i', video_path,
        '-filter_complex',
        '[0:v]split=3[v1][v2][v3];'
        '[v1]scale=w=854:h=480[vout1];'
        '[v2]scale=w=1280:h=720[vout2];'
        '[v3]scale=w=1920:h=1080[vout3]',
        '-map', '[vout1]',
        '-map', '[vout2]',
        '-map', '[vout3]',
        '-map', '0:a?',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-f', 'dash',
        '-use_template', '1',
        '-use_timeline', '1',
        '-init_seg_name', 'init-stream$RepresentationID$.m4s',
        '-media_seg_name', 'chunk-stream$RepresentationID$-$Number%05d$.m4s',
        '-seg_duration', '4',
        '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
        mpd_path
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        error_message = f"Error during segment generation: {e}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})
        raise Ignore()

    logger.info("Successfully generated DASH multi-resolution segment files")
    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})

    return {
        "video_uuid": video_uuid,
        "video_path": video_path,
        "segments_path": segments_path,
    }


@app.task(bind=True, name="extract_video_metadata", queue="medium_priority")
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


@app.task(bind=True, name="upload_segments_to_s3", max_retries=2, queue="medium_priority")
def upload_segments_to_s3(self, setup_data):
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


@app.task(bind=True, name="save_segments_to_db", queue="medium_priority")
def save_segments_to_db(self, setup_data):
    logger.info("Saving segments data to database.")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    video = Video.objects.get(uuid=setup_data["video_uuid"])
    segments_path = setup_data["segments_path"]

    for root, dirs, files in os.walk(segments_path):
        for file in files:
            segment_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(setup_data["video_uuid"]),
                                       'segments', file)
            VideoSegment.objects.create(video=video, segment_name=file, segment_url=segment_url)

    # Saving the mpd url of the s3 bucket
    video.mpd_file_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(setup_data["video_uuid"]),
                                      'segments', 'manifest.mpd')

    video.duration = setup_data.get("duration", 0)
    video.save()

    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})

    return setup_data


@app.task(bind=True, name="cleanup_files", queue="high_priority")
def cleanup_files(self, setup_data):
    logger.info("Cleaning up temporary files.")
    video_path = setup_data["video_path"]

    base_storage_path = settings.MEDIA_ROOT

    segments_parent_path = os.path.join(base_storage_path, 'stream_video', 'chunks', str(setup_data["video_uuid"]))

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
        setup_and_process_video.s(video_uuid, video_path).set(priority=1),  # Lowest priority
        extract_video_metadata.s().set(priority=6),  # Medium priority
        upload_segments_to_s3.s().set(priority=5),  # Medium priority
        save_segments_to_db.s().set(priority=6),  # Medium priority
        cleanup_files.s().set(priority=10)  # Highest priority
    )

    # Start the chain of tasks, no need to pass args here
    video_processing_chain.apply_async()


@app.task(bind=True, name="update_last_streamed_point", max_retries=1, queue="high_priority", priority=10)
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


@app.task(bind=True, name="cache_popular_segment_file", max_retries=1, queue="high_priority", priority=10)
def cache_popular_segment_file(self, video_uuid: str, segment_name: str):
    logger.info("Start caching the popular segment file")

    # Mark the task as "Processing"
    self.update_state(state=states.STARTED, meta={"status": "Processing"})

    try:
        # Fetch video segment from db
        segment: VideoSegment = VideoSegment.objects.select_related("video").get(
            video__uuid=video_uuid,
            segment_name=segment_name
        )
    except VideoSegment.DoesNotExist:
        error_message = f"Segment not found: {segment_name} for video {video_uuid}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})
        raise Ignore()  # Skip further processing

    if not segment.segment_url:
        warning_message = f"No segment_url found in DB for segment {segment_name}"
        logger.warn(warning_message)
        self.update_state(state=states.REJECTED, meta={"status": warning_message})
        raise Ignore()  # Skip further processing

    # Download segment file from the s3 bucket
    logger.info(f"Downloading the segment file {segment_name} before caching")
    try:
        response = requests.get(segment.segment_url, timeout=10)
        response.raise_for_status()
        segment_bytes = response.content
    except requests.RequestException as e:
        error_message = f"Failed to download segment {segment_name}: {e}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})

        retry_in = 10
        logger.info(f"Retrying in {retry_in} seconds...")
        raise self.retry(exc=e, countdown=retry_in)

    # Cache the segment file in redis
    logger.info("Caching the segment file in redis")
    segment_cache_key = f"segment_file:{video_uuid}:{segment_name}"
    redis_client.set(segment_cache_key, segment_bytes, ex=settings.CACHED_SEGMENT_EXPIRY)

    # Update is_cached flag in presigned_urls hash
    logger.info(f"Updating is_cached flag for the segment {segment_name}")

    presigned_urls_key = f"presigned_urls:{video_uuid}"
    try:
        segment_data_raw = redis_client.hget(presigned_urls_key, segment_name)
        if segment_data_raw:
            segment_data = json.loads(segment_data_raw)
            segment_data["is_cached"] = "true"
            redis_client.hset(presigned_urls_key, segment_name, json.dumps(segment_data))
            redis_client.expire(presigned_urls_key, settings.CACHED_SEGMENT_EXPIRY)
    except Exception as e:
        error_message = f"Failed to update is_cached flag for {segment_name}: {e}"
        logger.error(error_message)
        self.update_state(state=states.FAILURE, meta={"status": error_message})

    logger.info(f"Successfully cached segment {segment_name} for video {video_uuid}")
    self.update_state(state=states.SUCCESS, meta={"status": "Completed"})
    return "Task Successful"
