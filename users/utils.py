import secrets
from string import ascii_lowercase, ascii_uppercase, digits

from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import get_random_string


def create_random_password():
    """
    Creates a random password.
    """

    character_list = list(
        get_random_string(4, ascii_uppercase)
        + get_random_string(4, ascii_lowercase)
        + get_random_string(4, digits)
    )

    secrets._sysrand.shuffle(character_list)

    return "".join(character_list)


def get_permission_by_codename(codename: str):
    """
    Returns a permission object by its codename.

    Assumes all permissions are defined in ``Meta`` of the :class:`Permission` model.
    """

    from .models import Permission

    content_type = ContentType.objects.get_for_model(Permission)

    return Permission.objects.get(codename=codename, content_type=content_type)
