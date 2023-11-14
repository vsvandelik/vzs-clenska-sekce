import secrets
import string

from django.utils.crypto import get_random_string


def create_random_password():
    """
    Creates a random password.
    """

    character_list = list(
        get_random_string(4, string.ascii_uppercase)
        + get_random_string(4, string.ascii_lowercase)
        + get_random_string(4, string.digits)
    )

    secrets._sysrand.shuffle(character_list)

    return "".join(character_list)
