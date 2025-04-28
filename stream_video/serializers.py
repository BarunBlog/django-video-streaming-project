from django.core.exceptions import ObjectDoesNotExist
import os
from utils.presigned_urls import generate_presigned_url
from . import models
from rest_framework import serializers
from .models import Video, LastStreamedPoint, VideoSegment
from .validators import validate_video_file_extension
from utils.redis.redis_helpers import get_presigned_urls, cache_presigned_urls


class UploadVideoSerializer(serializers.ModelSerializer):
    video = serializers.FileField(validators=[validate_video_file_extension])

    class Meta:
        model = Video
        fields = ('title', 'description', 'category', 'video', 'thumbnail')


class GetVideosSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    last_streamed_second = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'uuid', 'author_name', 'title', 'category', 'thumbnail', 'created_at', 'last_streamed_second', 'duration'
        )

    def get_author_name(self, obj):
        return obj.author.username

    def get_last_streamed_second(self, obj):
        user_id = self.context.get("user_id", 0)

        try:
            # Get the Last Streamed Point object for the user
            last_streamed_point: LastStreamedPoint = models.get_last_streamed_point(
                user_id=user_id,
                video_uuid=obj.uuid
            )

            return last_streamed_point.last_played_second
        except ObjectDoesNotExist:
            return 0


class GetVideoDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    last_streamed_second = serializers.SerializerMethodField()
    presigned_urls = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'uuid', 'author_name', 'title', 'category', 'description', 'created_at', 'mpd_file_url',
            'last_streamed_second', 'presigned_urls'
        )

    def get_author_name(self, obj):
        return obj.author.username

    def get_last_streamed_second(self, obj):
        user_id = self.context.get("user_id", 0)

        try:
            # Get the Last Streamed Point object for the user
            last_streamed_point: LastStreamedPoint = models.get_last_streamed_point(
                user_id=user_id,
                video_uuid=obj.uuid
            )

            return last_streamed_point.last_played_second
        except ObjectDoesNotExist:
            return 0

    def get_presigned_urls(self, obj):
        print("Querying presigned urls for the video segments", flush=True)

        # Checking if redis has presigned urls cached for the video
        presigned_urls = get_presigned_urls(video_uuid=obj.uuid)
        if presigned_urls:
            print("Find presigned urls in the redis server", flush=True)
            return presigned_urls

        print("Generating presigned urls for the video segments", flush=True)

        segments = VideoSegment.objects.filter(video__uuid=obj.uuid).values('segment_name')
        presigned_urls = {}

        for segment in segments:
            s3_key = os.path.join('media', 'stream_video', 'chunks', str(obj.uuid), 'segments', segment["segment_name"])

            presigned_urls[segment["segment_name"]] = generate_presigned_url(s3_key)

        print("Caching the presigned urls into redis", flush=True)

        # Caching the presigned urls into redis
        cache_presigned_urls(video_uuid=obj.uuid, presigned_urls=presigned_urls)

        return presigned_urls


class UpdateLastStreamedPoint(serializers.Serializer):
    last_played_second = serializers.IntegerField(min_value=0, required=True)

    def validate_last_played_second(self, value):
        """
        Ensure last_played_second is a non-negative integer.
        """
        if value < 0:
            raise serializers.ValidationError("last_played_second must be a non-negative integer.")
        return value
