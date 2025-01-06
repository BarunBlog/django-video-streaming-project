from . import models
from rest_framework import serializers
from .models import Video, LastStreamedPoint
from .validators import validate_video_file_extension


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
        fields = ('uuid', 'author_name', 'title', 'category', 'thumbnail', 'created_at', 'last_streamed_second')

    def get_author_name(self, obj):
        return obj.author.username

    def get_last_streamed_second(self, obj):
        user_id = self.context.get("user_id", 0)

        # Get the Last Streamed Point object for the user
        last_streamed_point: LastStreamedPoint = models.get_last_streamed_point(user_id=user_id, video_uuid=obj.uuid)

        return last_streamed_point.last_played_second


class GetVideoDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    last_streamed_second = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'uuid', 'author_name', 'title', 'category', 'description', 'created_at', 'mpd_file_url',
            'last_streamed_second'
        )

    def get_author_name(self, obj):
        return obj.author.username

    def get_last_streamed_second(self, obj):
        user_id = self.context.get("user_id", 0)

        # Get the Last Streamed Point object for the user
        last_streamed_point: LastStreamedPoint = models.get_last_streamed_point(user_id=user_id, video_uuid=obj.uuid)

        return last_streamed_point.last_played_second
