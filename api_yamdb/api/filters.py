import django_filters
from django_filters import rest_framework
from reviews.models import Title


class TitleFilter(django_filters.FilterSet):
    category = rest_framework.CharFilter(field_name="category__slug")
    genre = rest_framework.CharFilter(field_name="genre__slug")
    name = rest_framework.CharFilter(
        field_name="name", lookup_expr="icontains"
    )

    class Meta:
        model = Title
        fields = {"year": ["exact"]}
