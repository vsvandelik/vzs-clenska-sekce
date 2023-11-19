from django.contrib.auth import models as auth_models
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token as BaseToken

from persons.models import Person
from vzs import settings
from vzs.models import RenderableModelMixin


class UserManager(auth_models.BaseUserManager):
    """
    A custom manager for the :class:`User` model.

    Provides utility methods for creating regular users and superusers.
    """

    def create_user(self, person, password=None):
        """
        Creates and saves a :class:`User` with the given person and password.
        """

        if not person:
            raise ValueError("Users must have a person set")

        if not isinstance(person, Person):
            person = Person.objects.get(pk=person)

        user = self.model(person=person)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, first_name, last_name, sex, person_type, password=None
    ):
        """
        Creates and saves a :class:`Person` with the given attributes. Also creates
        and saves a superuser for that person with the given password.
        """

        person = Person.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            person_type=person_type,
        )

        user = self.create_user(
            person,
            password=password,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(
    RenderableModelMixin, auth_models.AbstractUser, auth_models.PermissionsMixin
):
    """
    The model providing user functionality.

    Each user is associated with a :class:`Person` instance, which is its primary key.

    Users also have a password and a set of permissions.
    """

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


class Permission(RenderableModelMixin, auth_models.Permission):
    """
    Custom permission model with added description field.
    """

    class Meta:
        permissions = [("spravce_povoleni", _("Správce povolení"))]

    description = models.CharField(max_length=255)


class ResetPasswordToken(BaseToken):
    """
    Token for resetting a user's password through clicking a link in an email.
    """

    user: "User" = models.ForeignKey("users.User", on_delete=models.CASCADE)  # type: ignore

    @classproperty
    def has_expired(cls):
        """
        Returns a Q object for filtering expired tokens.
        """

        return Q(
            created__lt=timezone.now()
            - timezone.timedelta(hours=settings.RESET_PASSWORD_TOKEN_TTL_HOURS)
        )
