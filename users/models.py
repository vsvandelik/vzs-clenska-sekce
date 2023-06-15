from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.urls import reverse


class User(AbstractUser, PermissionsMixin):
    person = models.OneToOneField(
        "persons.Person", on_delete=models.CASCADE, primary_key=True
    )

    username = None
    first_name = None
    last_name = None
    email = None
    date_joined = None

    USERNAME_FIELD = "person"
    REQUIRED_FIELDS = []

    def clean(self):
        # A workaround.
        # If clean_fields() fails because there is a required field missing,
        # clean() gets called anyways and raises an exception
        # which doesn't get handled properly
        # TODO: find out if there is not a better way to do this

        if not hasattr(self, "person"):
            return

        super().clean()

    def __str__(self):
        return f"Uživatel pro Osobu {str(self.person)}"

    def get_absolute_url(self):
        return reverse("users:index")
        # TODO:
        # return reverse("users:detail", kwargs={"pk": self.pk})
