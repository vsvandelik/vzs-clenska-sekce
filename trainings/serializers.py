from trainings.models import Training

from rest_framework.serializers import ModelSerializer


class TrainingSerializer(ModelSerializer):
    class Meta:
        model = Training
        fields = "__all__"
