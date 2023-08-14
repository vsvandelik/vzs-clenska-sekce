from django.forms import ModelForm


class AgeLimitForm(ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data["min_age"] is not None
            and cleaned_data["max_age"] is not None
            and cleaned_data["min_age"] > cleaned_data["max_age"]
        ):
            self.add_error(
                "max_age",
                "Hodnota minimálního věku musí být menší nebo rovna hodnotě maximálního věku",
            )
        return cleaned_data


class GroupMembershipForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False
