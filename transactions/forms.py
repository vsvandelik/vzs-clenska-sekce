import datetime

from django import forms
from django.forms import ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

from vzs.widgets import DatePickerWithIcon
from .models import Transaction


class TransactionCreateEditBaseForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "reason", "date_due"]
        widgets = {
            "date_due": DatePickerWithIcon(),
        }

    amount = forms.IntegerField(
        min_value=1, label=Transaction._meta.get_field("amount").verbose_name
    )
    is_reward = forms.BooleanField(required=False, label=_("Je transakce odměna?"))

    def clean_date_due(self):
        date_due = self.cleaned_data["date_due"]

        if date_due < datetime.date.today():
            raise ValidationError(_("Datum splatnosti nemůže být v minulosti."))

        return date_due

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        is_reward = cleaned_data.get("is_reward")

        if not is_reward:
            cleaned_data["amount"] = -amount

        return cleaned_data


class TransactionCreateForm(TransactionCreateEditBaseForm):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person


class TransactionEditForm(TransactionCreateEditBaseForm):
    def __init__(self, instance, initial, *args, **kwargs):
        initial["is_reward"] = instance.amount > 0
        instance.amount = abs(instance.amount)

        super().__init__(instance=instance, initial=initial, *args, **kwargs)
