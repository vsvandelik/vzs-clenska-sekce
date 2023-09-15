from .models import Token

from django.forms import ModelForm


class TokenGenerateForm(ModelForm):
    class Meta:
        model = Token
        fields = []
