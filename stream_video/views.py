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
from django.db import transaction
from rest_framework import generics
from .serializers import GetVideosSerializer


class UploadVideo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadVideoSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            title = data.get('title')
            description = data.get('description')
            video_file = data.get('video')
            thumbnail = data.get('thumbnail')

            try:
                # Opening the database transaction ---------------------------------------------------------------------
                with transaction.atomic():

                    # Save the video metadata
                    video = Video.objects.create(
                        user=request.user,
                        title=title,
                        description=description,
                        thumbnail=thumbnail,
                    )

                    # Save the video temporarily to process it latter
                    # Note that video will be deleted after processing
                    video_path = os.path.join(settings.MEDIA_ROOT,
                                              'stream_video', 'videos', f"{str(video.uuid)}", f"{video_file.name}")
                    default_storage.save(video_path, video_file)

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


class ServeMPDFile(APIView):
    def get(self, request, *args, **kwargs):
        mpd_file_path = os.path.join(settings.STATIC_ROOT, 'stream_video', 'segments', 'manifest.mpd')
        print(mpd_file_path, flush=True)
        if os.path.exists(mpd_file_path):
            return FileResponse(open(mpd_file_path, 'rb'), content_type='application/dash+xml')
        else:
            raise Http404('MPD file not found')


class ServeSegmentFile(APIView):
    def get(self, request, segment_name, *args, **kwargs):
        segment_file_path = os.path.join(settings.STATIC_ROOT, 'stream_video', 'segments', segment_name)
        if os.path.exists(segment_file_path):
            return FileResponse(open(segment_file_path, 'rb'), content_type='video/mp4')
        else:
            raise Http404('Segment file not found')

