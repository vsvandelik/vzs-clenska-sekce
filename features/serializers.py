from .models import Feature

from rest_framework.serializers import ModelSerializer


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
