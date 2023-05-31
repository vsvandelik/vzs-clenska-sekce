from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin


class User(AbstractUser, PermissionsMixin):
    person = models.OneToOneField(
        'persons.Person', on_delete=models.CASCADE, primary_key=True)

    username = None
    first_name = None
    last_name = None
    email = None
    date_joined = None

    USERNAME_FIELD = 'person'
    REQUIRED_FIELDS = []
