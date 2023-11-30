from crispy_forms.helper import FormHelper


class DefaultFormHelper(FormHelper):
    pass


class WithoutFormTagFormHelper(FormHelper):
    disable_csrf = True
    form_tag = False


class WithoutFormTagMixin:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper = WithoutFormTagFormHelper()
