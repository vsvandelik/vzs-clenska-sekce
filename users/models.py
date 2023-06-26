from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.urls import reverse
from itertools import chain

from vzs.models import RenderableModelMixin
from persons.models import Person


class UserManager(BaseUserManager):
    def create_user(self, person, password=None):
        if not person:
            raise ValueError("Users must have a person set")

        if not isinstance(person, Person):
            person = Person.objects.get(pk=person)

        user = self.model(person=person)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, person, password=None):
        user = self.create_user(
            person,
            password=password,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(RenderableModelMixin, AbstractUser, PermissionsMixin):
    objects = UserManager()

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
        return f"Uživatel osoby {str(self.person)}"

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"pk": self.pk})

    def get_managed_persons(self):
        return list(chain(self.person.managed_persons.all(), [self.person]))
