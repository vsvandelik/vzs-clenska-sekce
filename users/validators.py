from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumNumericValidator:
    def validate(self, password, user=None):
        numeric_count = sum(c.isdigit() for c in password)

        if numeric_count == 0:
            raise ValidationError(
                _(f"Vaše heslo musí obsahovat alespoň jedno číslo."),
                code="password_no_numeric",
            )

    def get_help_text(self):
        return _(f"Vaše heslo musí obsahovat alespoň jedno číslo.")


class MinimumCapitalValidator:
    def validate(self, password, user=None):
        capital_count = sum(c.isalpha() and c.isupper() for c in password)

        if capital_count == 0:
            raise ValidationError(
                _(f"Vaše heslo musí obsahovat alespoň jedno velké písmeno."),
                code="password_no_capital",
            )

    def get_help_text(self):
        return _(f"Vaše heslo musí obsahovat alespoň jedno velkých písmeno.")
