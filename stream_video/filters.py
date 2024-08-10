import django_filters as filters
from .models import Video


class VideoFilter(filters.FilterSet):
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    category = filters.CharFilter(field_name='category', lookup_expr='iexact')
    created_at = filters.DateFilter(field_name='upload_date', lookup_expr='exact')

    class Meta:
        model = Video
        fields = ['title', 'category', 'created_at']
