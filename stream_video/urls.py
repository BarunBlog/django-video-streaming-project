from django.urls import path
from .views import UploadVideo, ServeMPDFile, ServeSegmentFile, GetVideos, GetVideoDetail, UpdateLastStreamedPointApi, \
    SaveSegmentActivityApi

urlpatterns = [
    path('upload-video/', UploadVideo.as_view(), name='upload-video'),
    path('get-videos/', GetVideos.as_view(), name='get-videos'),
    path('get-videos/<uuid:uuid>/', GetVideoDetail.as_view(), name='get-video-detail'),
    path('stream/<uuid:video_uuid>/update-last-streamed-point/', UpdateLastStreamedPointApi.as_view(),
         name='update-last-streamed-point'),
    path('stream/<uuid:video_uuid>/save-segment-activity/', SaveSegmentActivityApi.as_view(),
         name='save-segment-activity'),
    path('stream/<uuid:video_uuid>/', ServeMPDFile.as_view(), name='serve_mpd_file'),
    path('stream/<uuid:video_uuid>/<str:segment_name>/', ServeSegmentFile.as_view(),
         name='serve_segment_file'),
]
