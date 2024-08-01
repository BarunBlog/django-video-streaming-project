from django_filters import rest_framework as filters
from .models import Video


class VideoFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category', lookup_expr='iexact')

    class Meta:
        model = Video
        fields = ['category']
