import django_filters as filters
from .models import Video


class VideoFilter(filters.FilterSet):
    except_video_uuid = filters.UUIDFilter(method='filter_except_video_uuid')
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    category = filters.CharFilter(field_name='category', lookup_expr='iexact')
    created_at = filters.DateFilter(field_name='upload_date', lookup_expr='exact')

    class Meta:
        model = Video
        fields = ['title', 'category', 'created_at']

    def filter_except_video_uuid(self, queryset, name, value):
        # Exclude the video with the given UUID from the queryset
        return queryset.exclude(uuid=value)
