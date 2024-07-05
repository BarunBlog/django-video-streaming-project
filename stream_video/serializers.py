from rest_framework import serializers
from .models import Video
from .validators import validate_video_file_extension


class UploadVideoSerializer(serializers.ModelSerializer):

    video = serializers.FileField(validators=[validate_video_file_extension])

    class Meta:
        model = Video
        fields = ('title', 'description', 'video', 'thumbnail')
