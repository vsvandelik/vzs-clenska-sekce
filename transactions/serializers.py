from transactions.models import Transaction

from rest_framework.serializers import ModelSerializer


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
