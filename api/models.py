from rest_framework.authtoken.models import Token as BaseToken

from django.utils.translation import gettext_lazy as _
from django.db import models


class Token(BaseToken):
    user = None
    name = models.CharField(_("Název"), max_length=50)
