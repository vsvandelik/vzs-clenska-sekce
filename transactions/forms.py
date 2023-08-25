import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div
from django import forms
from django.forms import ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

from persons.forms import PersonsFilterForm
from persons.widgets import PersonSelectWidget
from vzs.widgets import DatePickerWithIcon
from .models import Transaction
from .utils import parse_transactions_filter_queryset


class TransactionCreateEditMixin(ModelForm):
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


class TransactionCreateFromPersonForm(TransactionCreateEditMixin):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person


class TransactionCreateBulkForm(TransactionCreateEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attach_person_filter_form()
        self._prepare_transaction_form()

    def _attach_person_filter_form(self):
        person_filter_form = PersonsFilterForm()

        for field_name, field in person_filter_form.fields.items():
            self.fields[field_name] = field

        self.filter_helper = FormHelper()
        self.filter_helper.form_tag = False

        # Remove submit button and background from person filter form
        person_filter_form_layout_rows = person_filter_form.helper.layout.fields[
            0
        ].fields

        self.filter_helper.layout = Layout(
            person_filter_form_layout_rows[0],
            person_filter_form_layout_rows[1],
            person_filter_form_layout_rows[2],
        )

    def _prepare_transaction_form(self):
        self.transaction_helper = FormHelper()
        self.transaction_helper.form_tag = False
        self.transaction_helper.layout = Layout(
            "amount", "reason", "date_due", "is_reward"
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data = PersonsFilterForm.clean_with_given_values(cleaned_data)


class TransactionCreateEditPersonSelectMixin(TransactionCreateEditMixin):
    class Meta(TransactionCreateEditMixin.Meta):
        fields = ["person"] + TransactionCreateEditMixin.Meta.fields
        widgets = TransactionCreateEditMixin.Meta.widgets
        widgets["person"] = PersonSelectWidget()


class TransactionCreateForm(TransactionCreateEditPersonSelectMixin):
    pass


class TransactionEditForm(TransactionCreateEditPersonSelectMixin):
    def __init__(self, instance, initial, *args, **kwargs):
        initial["is_reward"] = instance.amount > 0
        instance.amount = abs(instance.amount)

        super().__init__(instance=instance, initial=initial, *args, **kwargs)


class TransactionFilterForm(forms.Form):
    person_name = forms.CharField(label=_("Jméno osoby obsahuje"), required=False)
    reason = forms.CharField(label=_("Popis obsahuje"), required=False)
    transaction_type = forms.ChoiceField(
        label=_("Typ transakce"),
        required=False,
        choices=[("", "---------")] + [("reward", "Odměna"), ("debt", "Dluh")],
    )
    is_settled = forms.ChoiceField(
        label=_("Transakce zaplacena"),
        required=False,
        choices=[("", "---------")] + [("paid", "Ano"), ("not paid", "Ne")],
    )
    amount_from = forms.IntegerField(label=_("Suma od"), required=False, min_value=1)
    amount_to = forms.IntegerField(label=_("Suma do"), required=False, min_value=1)
    date_due_from = forms.DateField(label=_("Datum splatnosti od"), required=False)
    date_due_to = forms.DateField(label=_("Datum splatnosti do"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.form_id = "transactions-filter-form"
        self.helper.layout = Layout(
            Div(
                Div(
                    Div("person_name", css_class="col-md-4"),
                    Div("reason", css_class="col-md-4"),
                    Div("transaction_type", css_class="col-md-2"),
                    Div("is_settled", css_class="col-md-2"),
                    css_class="row",
                ),
                Div(
                    Div("amount_from", css_class="col-md-3"),
                    Div("amount_to", css_class="col-md-3"),
                    Div("date_due_from", css_class="col-md-3"),
                    Div("date_due_to", css_class="col-md-3"),
                    css_class="row",
                ),
                Div(
                    Div(
                        Submit(
                            "submit",
                            "Filtrovat",
                            css_class="btn btn-primary float-right",
                        ),
                        css_class="col-12",
                    ),
                    css_class="row",
                ),
                css_class="p-2 border rounded bg-light",
                style="box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.05);",
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        amount_from = cleaned_data.get("amount_from")
        amount_to = cleaned_data.get("amount_to")
        date_due_from = cleaned_data.get("date_due_from")
        date_due_to = cleaned_data.get("date_due_to")

        if amount_from and amount_to and amount_from > amount_to:
            raise ValidationError(_("Suma od musí být menší nebo rovna sumě do."))

        if date_due_from and date_due_to and date_due_from > date_due_to:
            raise ValidationError(
                _("Datum splatnosti od musí být menší nebo roven datumu splatnosti do.")
            )

    def process_filter(self):
        transactions = Transaction.objects.all()

        if not self.is_valid():
            return transactions

        return parse_transactions_filter_queryset(self.cleaned_data, transactions)
