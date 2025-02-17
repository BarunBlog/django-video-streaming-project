import os
import re
import requests
from django.conf import settings
from rest_framework.views import APIView
from django.http import StreamingHttpResponse, HttpResponse, FileResponse, Http404, JsonResponse
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import UploadVideoSerializer, UpdateLastStreamedPoint
from .tasks import update_last_streamed_segment, process_video
from .models import Video, VideoSegment, get_video_by_uuid
from .filters import VideoFilter
from django.db import transaction
from rest_framework import generics
from .serializers import GetVideosSerializer, GetVideoDetailSerializer
from django.core.exceptions import ObjectDoesNotExist
from django_filters import rest_framework as filters
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)


# Key is used as the user as the api is authenticated must
# Rate is 2 requests per 1 minutes
# If the limit is exceeded, the user will be blocked
@method_decorator(ratelimit(key='user', rate='2/m', block=True), name='dispatch')
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

                    # Determine storage directory (NFS in production, local in other environments)
                    if settings.ENVIRONMENT == "staging":
                        base_storage_path = settings.NFS_ROOT_URL + 'stream_video/videos'
                    else:
                        base_storage_path = os.path.join(settings.MEDIA_ROOT, 'stream_video', 'videos')

                    # Create the directory for saving the video if it doesn't exist
                    video_directory = os.path.join(base_storage_path, str(video.uuid))
                    os.makedirs(video_directory, exist_ok=True)

                    # Define the full path for the video file
                    video_path = os.path.join(video_directory, video_file.name)

                    # Save the file to the defined path
                    with open(video_path, 'wb+') as destination:
                        for chunk in video_file.chunks():
                            destination.write(chunk)

                    # Call the Celery task to process the video
                    process_video(video.uuid, video_path)
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"user_id": self.request.user.id})
        return context


class GetVideoDetail(generics.RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = GetVideoDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"user_id": self.request.user.id})
        return context


# Key is used as the user as the api is authenticated must
# Rate is 10 requests per 1 minutes
# If the limit is exceeded, the user will be blocked
@method_decorator(ratelimit(key='user', rate='10/m', block=True), name='dispatch')
class ServeMPDFile(APIView):

    def get(self, request, video_uuid, *args, **kwargs):

        # Get video object by uuid
        try:
            video: Video = Video.objects.get(uuid=video_uuid)
        except  Video.objects.get:
            return Response({"message": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

        if not video.mpd_file_url:
            return Response({"message": "Video mpd file url not found"}, status=status.HTTP_404_NOT_FOUND)

        environment = settings.ENVIRONMENT

        try:
            mpd_file_url = video.mpd_file_url

            if environment == "development":
                mpd_file_url = "http://backend-nginx-1:80" + mpd_file_url

            response = requests.get(mpd_file_url, stream=True)

            if response.status_code == 200:
                return HttpResponse(response.content, content_type='application/dash+xml')
            else:
                return Response({"message": "Failed to retrieve the MPD file"}, status=status.HTTP_404_NOT_FOUND)
        except requests.RequestException as e:
            return Response({"message": f"Error retrieving video MPD file: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Key is used as the user as the api is authenticated must
# Rate is 600 requests per 10 minutes
# If the limit is exceeded, the user will be blocked
@method_decorator(ratelimit(key='user', rate='600/10m', block=True), name='dispatch')
class ServeSegmentFile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, video_uuid, segment_name, *args, **kwargs):
        environment = settings.ENVIRONMENT

        last_played_second = request.query_params.get("playbackTime", None)

        try:
            web_host = settings.WEB_HOST
            web_port = settings.WEB_PORT

            domain = f'http://{web_host}:{web_port}'

            if environment == "production":
                segment_file_url = os.path.join(settings.MEDIA_URL, 'stream_video', 'chunks', str(video_uuid),
                                                'segments',
                                                segment_name)
            else:
                segment_file_url = os.path.join(domain, 'media', 'stream_video', 'chunks', str(video_uuid), 'segments',
                                                segment_name)

            response = requests.get(segment_file_url, stream=True)

            if response.status_code == 200:
                # Saving the last streamed point for the user using celery worker
                if last_played_second:
                    update_last_streamed_segment.delay(
                        user_id=request.user.id, video_uuid=video_uuid, last_played_second=last_played_second
                    )

                return HttpResponse(response.content, content_type='application/dash+xml')
            else:
                return Response({"message": "Failed to retrieve the MPD file"}, status=status.HTTP_404_NOT_FOUND)

        except requests.RequestException as e:
            return Response({"message": f"Error retrieving video MPD file: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateLastStreamedPointApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        serializer = UpdateLastStreamedPoint(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        last_played_second = serializer.validated_data['last_played_second']

        # Fetch the video object dynamically using the UUID
        video_uuid = kwargs.get('video_uuid')
        if not video_uuid:
            return Response({"error": "Video UUID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Saving the last streamed point for the user using celery worker
        update_last_streamed_segment.delay(
            user_id=request.user.id, video_uuid=video_uuid, last_played_second=last_played_second
        )

        return Response({"message": "mpd_url updated successfully."}, status=status.HTTP_200_OK)
