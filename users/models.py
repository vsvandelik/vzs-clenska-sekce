from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import Permission as BasePermission
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token as BaseToken

from persons.models import Person
from vzs import settings
from vzs.models import RenderableModelMixin
from vzs.settings import CURRENT_DATETIME


class UserManager(BaseUserManager):
    """
    A custom manager for the :class:`User` model.

    Provides utility methods for creating regular users and superusers.
    """

    def create_user(self, person, password=None):
        """
        Creates and saves a :class:`User` with the given person and password.
        """

        if person is None:
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
        Creates and saves a :class:`persons.models.Person` with the given attributes.
        Also creates and saves a superuser for that person with the given password.
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


class User(RenderableModelMixin, AbstractUser, PermissionsMixin):
    """
    The model providing user functionality.

    Each user is associated with a :class:`persons.models.Person` instance,
    which is its primary key.

    Users also have a password and a set of permissions.
    """

    objects = UserManager()

    person = models.OneToOneField(
        "persons.Person", on_delete=models.CASCADE, primary_key=True
    )

    username = None
    """:meta private:"""
    first_name = None
    """:meta private:"""
    last_name = None
    """:meta private:"""
    email = None
    """:meta private:"""
    date_joined = None
    """:meta private:"""

    USERNAME_FIELD = "person"
    """:meta private:"""

    REQUIRED_FIELDS = []
    """:meta private:"""

    def clean(self):
        """:meta private:"""

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


class Permission(RenderableModelMixin, BasePermission):
    """
    Custom permission model with added description field.
    """

    class Meta:
        permissions = [
            ("povoleni", _("Správce povolení")),
            ("kvalifikace", _("Správce kvalifikací")),
            ("opravneni", _("Správce oprávnění")),
            ("vybaveni", _("Správce vybavení")),
            ("skupiny", _("Správce skupin")),
            ("stranky", _("Správce textových stránek")),
            ("komercni_udalosti", _("Správce komerčních událostí")),
            ("kurzy", _("Správce kurzů")),
            ("prezentacni_udalosti", _("Správce prezentačních událostí")),
            ("udalosti_pro_deti", _("Správce událostí pro děti")),
            ("spolecenske_udalosti", _("Správce společenských událostí")),
            ("lezecke_treninky", _("Správce lezeckých tréninků")),
            ("plavecke_treninky", _("Správce plaveckých tréninků")),
            ("zdravoveda", _("Správce zdravovědy")),
            ("clenska_zakladna", _("Správce členské základny")),
            ("detska_clenska_zakladna", _("Správce dětské členské základny")),
            (
                "bazenova_clenska_zakladna",
                _("Správce bazénové dětské členské základny"),
            ),
            (
                "lezecka_clenska_zakladna",
                _("Správce lezecké dětské členské základny"),
            ),
            ("dospela_clenska_zakladna", _("Správce dospělé členské základny")),
            ("transakce", _("Správce transakcí")),
        ]

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
            created__lt=CURRENT_DATETIME()
            - timezone.timedelta(hours=settings.RESET_PASSWORD_TOKEN_TTL_HOURS)
        )
