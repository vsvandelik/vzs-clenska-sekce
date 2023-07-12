from django.utils.crypto import get_random_string

import secrets
import string


def get_random_password():
    character_list = list(
        get_random_string(4, string.ascii_uppercase)
        + get_random_string(4, string.ascii_lowercase)
        + get_random_string(4, string.digits)
    )

    secrets._sysrand.shuffle(character_list)

    return "".join(character_list)
