from django.urls import path
from .views import UploadVideo, ServeMPDFile, ServeSegmentFile, GetVideos, GetVideoDetail

urlpatterns = [
    path('upload-video/', UploadVideo.as_view(), name='upload-video'),
    path('get-videos/', GetVideos.as_view(), name='get-videos'),
    path('get-videos/<uuid:uuid>/', GetVideoDetail.as_view(), name='get-video-detail'),
    path('stream-video/', ServeMPDFile.as_view(), name='serve_mpd_file'),
    path('stream-video/<str:segment_name>/', ServeSegmentFile.as_view(), name='serve_segment_file'),
]
