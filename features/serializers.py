from .models import Feature

from rest_framework.serializers import ModelSerializer


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        exclude = ["lft", "rght", "tree_id", "level"]
