from django.db import models
from django.contrib.auth.models import User
import uuid

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
    mpd_file_url = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


class VideoSegment(models.Model):
    video = models.ForeignKey(Video, related_name='segments', on_delete=models.CASCADE)
    segment_name = models.CharField(max_length=255)
    segment_url = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.video.title} - {self.segment_name}"
