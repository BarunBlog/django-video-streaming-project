from django.db import models
from django.contrib.auth.models import User
import uuid


class Video(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mpd_file_url = models.URLField(max_length=255)

    def __str__(self):
        return self.title


class VideoSegment(models.Model):
    video = models.ForeignKey(Video, related_name='segments', on_delete=models.CASCADE)
    segment_name = models.CharField(max_length=255)
    segment_url = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.video.title} - {self.segment_name}"
