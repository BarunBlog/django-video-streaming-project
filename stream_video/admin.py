from django.contrib import admin
from .models import Video, VideoSegment, LastStreamedSegment


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'title', 'author', 'category', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username')


@admin.register(VideoSegment)
class VideoSegmentAdmin(admin.ModelAdmin):
    list_display = ('video', 'segment_name')
    search_fields = ('video__title', 'segment_name')


@admin.register(LastStreamedSegment)
class LastStreamedSegmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'last_segment', 'updated_at')
