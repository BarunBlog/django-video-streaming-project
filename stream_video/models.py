from django.db import models
from django.contrib.auth.models import User
import uuid
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

logger = logging.getLogger(__name__)

CATEGORY_CHOICES = [
    ('Education', 'Education'),
    ('Entertainment', 'Entertainment'),
    ('Music', 'Music'),
    ('News', 'News'),
    ('Sports', 'Sports'),
    ('Technology', 'Technology'),
    ('Gaming', 'Gaming'),
    ('Other', 'Other'),
]


class Video(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to="stream_video/images/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mpd_file_url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


def get_video_by_uuid(video_uuid: str) -> Video:
    logger.info("Start getting the video by uuid")

    try:
        video: Video = Video.objects.get(uuid=video_uuid)
        logger.info("Video found: %s", video.title)
        return video

    except Video.DoesNotExist:
        logger.error("Video with UUID %s does not exist", video_uuid)
        raise ObjectDoesNotExist(f"Video with UUID {video_uuid} does not exist.")


class VideoSegment(models.Model):
    video = models.ForeignKey(Video, related_name='segments', on_delete=models.CASCADE)
    segment_name = models.CharField(max_length=255)
    segment_url = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.video.title} - {self.segment_name}"


def get_video_segment_by_name(video: Video, segment_name: str) -> VideoSegment:
    logger.info("Start getting video segment by name")

    try:
        video_segment: VideoSegment = VideoSegment.objects.get(video=video, segment_name=segment_name)

        logger.info("Video segment found: %s", video_segment.segment_name)
        return video_segment

    except VideoSegment.DoesNotExist:
        logger.error("Video segment with name %s does not exist", segment_name)
        raise ObjectDoesNotExist(f"Video segment with name {segment_name} does not exist.")


class LastStreamedPoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_points')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='stream_points')
    last_played_second = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


def save_last_streamed_segment(user_id: int, video: Video, last_played_second: int) -> LastStreamedPoint:
    logger.info("Start saving last streamed segment by the user")

    try:
        # Create or update the last streamed segment
        obj, created = LastStreamedPoint.objects.update_or_create(
            user_id=user_id, video=video, defaults={'last_played_second': last_played_second}
        )

        if created:
            logger.info("Created a new LastStreamedPoint for user_id %s and video %s.", user_id, video.title)
        else:
            logger.info("Updated the last streamed segment for user_id %s and video %s.", user_id, video.title)

        return obj

    except DatabaseError as e:
        logger.exception("Database error occurred while saving last streamed segment for user_id %s and video %s.",
                         user_id, video.title)
        raise e
