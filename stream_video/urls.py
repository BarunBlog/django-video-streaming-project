from django.urls import path
from .views import StreamVideo, ServeMPDFile, ServeSegmentFile

urlpatterns = [
    # path('stream-video/', StreamVideo.as_view(), name='stream_video'),
    path('stream-video/', ServeMPDFile.as_view(), name='serve_mpd_file'),
    path('stream-video/<str:segment_name>/', ServeSegmentFile.as_view(), name='serve_segment_file'),
]
