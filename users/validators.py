from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumNumericValidator:
    """
    Validates that the password contains at least one numeric character.
    """

    def validate(self, password, user=None):
        """:meta private:"""

        numeric_count = sum(c.isdigit() for c in password)

        if numeric_count == 0:
            raise ValidationError(
                _(f"Vaše heslo musí obsahovat alespoň jedno číslo."),
                code="password_no_numeric",
            )

    def get_help_text(self):
        """:meta private:"""

        return _(f"Vaše heslo musí obsahovat alespoň jedno číslo.")


class MinimumCapitalValidator:
    """
    Validates that the password contains at least one capital letter.
    """

    def validate(self, password, user=None):
        """:meta private:"""

        capital_count = sum(c.isalpha() and c.isupper() for c in password)

        if capital_count == 0:
            raise ValidationError(
                _(f"Vaše heslo musí obsahovat alespoň jedno velké písmeno."),
                code="password_no_capital",
            )

    def get_help_text(self):
        """:meta private:"""

        return _(f"Vaše heslo musí obsahovat alespoň jedno velkých písmeno.")
