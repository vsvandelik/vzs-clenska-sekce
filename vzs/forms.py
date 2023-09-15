from crispy_forms.helper import FormHelper


class DefaultFormHelper(FormHelper):
    pass


class WithoutFormTagFormHelper(FormHelper):
    disable_csrf = True
    form_tag = False
