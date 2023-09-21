from .models import Feature

from rest_framework.serializers import HyperlinkedModelSerializer


class FeatureSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Feature
        exclude = ["lft", "rght", "tree_id", "level"]
        extra_kwargs = {
            "url": {"view_name": "api:feature-detail"},
            "parent": {"view_name": "api:feature-detail"},
        }
