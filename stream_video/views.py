import os
import re
from django.conf import settings
from rest_framework.views import APIView
from django.http import StreamingHttpResponse, HttpResponse, FileResponse, Http404
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import UploadVideoSerializer
from django.core.files.storage import default_storage
from .tasks import process_video
from .models import Video
from .filters import VideoFilter
from django.db import transaction
from rest_framework import generics
from .serializers import GetVideosSerializer, GetVideoDetailSerializer
from django.core.exceptions import ObjectDoesNotExist
from django_filters import rest_framework as filters


class UploadVideo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadVideoSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            title = data.get('title')
            description = data.get('description')
            category = data.get('category')
            video_file = data.get('video')
            thumbnail = data.get('thumbnail')

            try:
                # Opening the database transaction ---------------------------------------------------------------------
                with transaction.atomic():

                    # Save the video metadata
                    video: Video = Video.objects.create(
                        author=request.user,
                        title=title,
                        description=description,
                        category=category,
                        thumbnail=thumbnail,
                    )

                    # Create the directory for saving the video if it doesn't exist
                    video_directory = os.path.join(settings.MEDIA_ROOT, 'stream_video', 'videos', str(video.uuid))
                    os.makedirs(video_directory, exist_ok=True)

                    # Define the full path for the video file
                    video_path = os.path.join(video_directory, video_file.name)

                    # Save the file to the defined path
                    with open(video_path, 'wb+') as destination:
                        for chunk in video_file.chunks():
                            destination.write(chunk)

                    # Call the Celery task to process the video
                    process_video.delay(video_uuid=str(video.uuid), video_path=video_path)

                    return Response({"message": "Video uploaded successfully. Processing in background."},
                                    status=status.HTTP_201_CREATED)

            except IntegrityError as err:
                print(err)
                return Response({"message": "Failed to upload the video"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetVideos(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = GetVideosSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = VideoFilter


class GetVideoDetail(generics.RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = GetVideoDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'


class ServeMPDFile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, video_uuid, *args, **kwargs):

        # Get video object by uuid
        try:
            video: Video = Video.objects.get(uuid=video_uuid)
        except ObjectDoesNotExist:
            return Response({"message": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

        if not video.mpd_file_url:
            return Response({"message": "Video mpd file url not found"}, status=status.HTTP_404_NOT_FOUND)

        if os.path.exists(video.mpd_file_url):
            return FileResponse(open(video.mpd_file_url, 'rb'), content_type='application/dash+xml')
        else:
            return Response({"message": "Video mpd file not found"}, status=status.HTTP_404_NOT_FOUND)


class ServeSegmentFile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, video_uuid, segment_name, *args, **kwargs):
        segment_file_path = os.path.join(
            settings.MEDIA_ROOT, 'stream_video', 'chunks', str(video_uuid), 'segments', segment_name)
        if os.path.exists(segment_file_path):
            return FileResponse(open(segment_file_path, 'rb'), content_type='video/mp4')
        else:
            return Response({"message": "Video segment file not found"}, status=status.HTTP_404_NOT_FOUND)
