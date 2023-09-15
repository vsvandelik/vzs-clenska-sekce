from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token as BaseToken


class Token(BaseToken):
    user = None
