from django.contrib import admin
from .models import Video, VideoSegment


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username')


@admin.register(VideoSegment)
class VideoSegmentAdmin(admin.ModelAdmin):
    list_display = ('video', 'segment_name')
    search_fields = ('video__title', 'segment_name')
