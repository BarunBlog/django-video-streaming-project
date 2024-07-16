from rest_framework import serializers
from .models import Video
from .validators import validate_video_file_extension


class UploadVideoSerializer(serializers.ModelSerializer):
    video = serializers.FileField(validators=[validate_video_file_extension])

    class Meta:
        model = Video
        fields = ('title', 'description', 'video', 'thumbnail')


class GetVideosSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('uuid', 'author_name', 'title', 'thumbnail', 'created_at')

    def get_author_name(self, obj):
        return obj.author.username


class GetVideoDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('uuid', 'author_name', 'title', 'description', 'created_at', 'mpd_file_url')

    def get_author_name(self, obj):
        return obj.author.username
