import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Row, Column
from django import forms
from django.forms import ModelForm, ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from events.forms_bases import InsertRequestIntoSelf
from persons.forms import PersonsFilterForm
from persons.widgets import PersonSelectWidget
from vzs.forms import WithoutFormTagFormHelper
from vzs.utils import send_notification_email
from vzs.widgets import DatePickerWithIcon
from .models import Transaction, BulkTransaction
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
        self.helper = WithoutFormTagFormHelper()


class TransactionCreateBulkForm(TransactionCreateEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attach_person_filter_form()
        self._prepare_transaction_form()

    def _attach_person_filter_form(self):
        person_filter_form = PersonsFilterForm()

        for field_name, field in person_filter_form.fields.items():
            self.fields[field_name] = field

        self.filter_helper = WithoutFormTagFormHelper()

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
        self.transaction_helper = WithoutFormTagFormHelper()
        self.transaction_helper.layout = Layout(
            "amount", "reason", "date_due", "is_reward"
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data = PersonsFilterForm.clean_with_given_values(cleaned_data)

        return cleaned_data


class TransactionAddTrainingPaymentForm(forms.Form):
    date_due = forms.DateField(label=_("Datum splatnosti"), widget=DatePickerWithIcon())
    reason = forms.CharField(label=_("Popis transakce"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event", 0)
        super().__init__(*args, **kwargs)

        for i in range(1, self.event.weekly_occurs_count() + 1):
            self.fields[f"amount_{i}"] = forms.IntegerField(
                label=_("Suma za trénink {0}x týdně").format(i),
                min_value=1,
            )

        self.initial["reason"] = _("Platba za tréninky - {0}").format(self.event)


class Label:
    def __init__(self, text=None):
        self.text = text

    def render(self, form, context, template_pack, extra_context=None, **kwargs):
        if not self.text:
            return ""

        return f"<label class='col-form-label'>{self.text}</label>"


class TransactionCreateBulkConfirmForm(InsertRequestIntoSelf, forms.Form):
    def __init__(self, *args, **kwargs):
        persons_transactions = kwargs.pop("persons_transactions", [])
        self.event = kwargs.pop("event", None)
        self.reason = kwargs.pop("reason", [])

        super().__init__(*args, **kwargs)

        layout_divs = []
        self._add_fields_by_persons_transactions_list(persons_transactions, layout_divs)
        self._prepare_form_helper(layout_divs)

        self.persons_transactions = persons_transactions
        self.prepared_transactions = []

    def _add_fields_by_persons_transactions_list(
        self, persons_transactions, layout_divs
    ):
        for transaction in persons_transactions:
            person = transaction["person"]
            field_name_amount = f"transactions-{person.id}-amount"
            field_name_date_due = f"transactions-{person.id}-date_due"

            self.fields[field_name_amount] = forms.IntegerField(
                required=False, initial=transaction["amount"]
            )
            self.fields[field_name_date_due] = forms.DateField(
                required=False,
                initial=transaction["date_due"],
                widget=DatePickerWithIcon(),
            )

            layout_divs.append(
                Row(
                    Column(Label(person), css_class="col-md-4"),
                    Column(field_name_amount, css_class="col-md-4"),
                    Column(field_name_date_due, css_class="col-md-4"),
                    css_class="row",
                ),
            )

    def _prepare_form_helper(self, layout_divs):
        self.helper = WithoutFormTagFormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column(Label(), css_class="col-md-4"),
                Column(Label(_("Částka")), css_class="col-md-4 text-center"),
                Column(Label(_("Datum splatnosti")), css_class="col-md-4 text-center"),
                css_class="row",
            ),
            *layout_divs,
        )

    def clean(self):
        cleaned_data = super().clean()

        for person_transaction in self.persons_transactions:
            person = person_transaction["person"]
            field_name_amount = f"transactions-{person.id}-amount"
            field_name_date_due = f"transactions-{person.id}-date_due"

            amount = cleaned_data.get(field_name_amount)
            date_due = cleaned_data.get(field_name_date_due)

            if not amount or amount == 0:
                cleaned_data.pop(field_name_amount)
                cleaned_data.pop(field_name_date_due)
            elif not date_due:
                self.add_error(
                    field_name_date_due, _("Datum splatnosti musí být vyplněno.")
                )
            elif date_due < datetime.date.today():
                self.add_error(
                    field_name_date_due, _("Datum splatnosti nemůže být v minulosti.")
                )
            else:
                self.prepared_transactions.append(
                    (
                        Transaction(
                            person=person,
                            amount=amount,
                            reason=self.reason,
                            date_due=date_due,
                            event=self.event,
                        ),
                        person_transaction["enrollment"],
                    )
                )

        return cleaned_data

    def create_transactions(self):
        bulk_transaction = BulkTransaction(reason=self.reason, event=self.event)
        bulk_transaction.save()

        for transaction, enrollment in self.prepared_transactions:
            transaction.bulk_transaction = bulk_transaction
            transaction.save()
            enrollment.transactions.add(transaction)
            self.send_new_transaction_email(enrollment, transaction)

    def send_new_transaction_email(self, enrollment, transaction):
        qr_uri = self.request.build_absolute_uri(
            reverse("transactions:qr", args=(transaction.pk,))
        )

        payment_info = f'<br><br>Prosím provedte platbu dle instrukcí viz <a href="{qr_uri}">{qr_uri}</a>'
        send_notification_email(
            _("Nová transakce k zaplacení"),
            _(
                f"U události {enrollment.event} byla vytvořena nová transakce k zaplacení.{payment_info}"
            ),
            [enrollment.person],
        )


class TransactionCreateEditPersonSelectMixin(TransactionCreateEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = WithoutFormTagFormHelper()
        self.helper.include_media = False

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
    bulk_transaction = forms.ModelChoiceField(
        label=_("Hromadná transakce"),
        queryset=BulkTransaction.objects.all(),
        required=False,
        widget=Select2Widget,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.form_id = "transactions-filter-form"
        self.helper.include_media = False
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
                    Div("amount_from", css_class="col-md-2"),
                    Div("amount_to", css_class="col-md-2"),
                    Div("date_due_from", css_class="col-md-2"),
                    Div("date_due_to", css_class="col-md-2"),
                    Div("bulk_transaction", css_class="col-md-4"),
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
