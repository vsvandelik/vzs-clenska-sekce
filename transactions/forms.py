from collections.abc import Iterable, MutableMapping
from typing import Any

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Div, Layout, Row, Submit
from django.db.models import QuerySet
from django.forms import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    Form,
    IntegerField,
    ModelChoiceField,
    ModelForm,
    RadioSelect,
    ValidationError,
)
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from events.forms_bases import InsertRequestIntoSelf
from events.models import Event, ParticipantEnrollment
from persons.forms import PersonsFilterForm
from persons.models import Person
from persons.widgets import PersonSelectWidget
from trainings.models import Training
from vzs.datetime_constants import MONTH_NAMES
from vzs.forms import WithoutFormTagFormHelper, WithoutFormTagMixin
from vzs.utils import (
    filter_queryset,
    payment_email_html,
    send_notification_email,
    today,
)
from vzs.widgets import DatePickerWithIcon

from .models import BulkTransaction, Transaction
from .utils import TransactionFilter, TransactionInfo


class TransactionCreateEditFormMixin(ModelForm):
    """
    A mixin form for creating and editing transactions.

    **Request parameters:**

    *   ``amount``
    *   ``reason``
    *   ``date_due``
    *   ``reward_type``
    """

    RewardChoices = [("reward", "Odměna"), ("debt", "Dluh")]

    class Meta:
        model = Transaction
        fields = ["amount", "reason", "date_due"]
        widgets: MutableMapping[str, Any] = {
            "date_due": DatePickerWithIcon(),
        }

    amount = IntegerField(
        min_value=1, label=Transaction._meta.get_field("amount").verbose_name
    )
    reward_type = ChoiceField(
        choices=RewardChoices, label=_("Typ transakce"), widget=RadioSelect
    )

    field_order = ["reward_type", "amount", "reason", "date_due"]

    def clean_date_due(self):
        """
        Validates that the due date is not in the past.
        """

        date_due = self.cleaned_data["date_due"]

        if date_due < today():
            raise ValidationError(_("Datum splatnosti nemůže být v minulosti."))

        return date_due

    def clean(self):
        """
        Saves the amount as a negative number if it is not a reward (=> a debt).
        """

        cleaned_data = super().clean()

        amount = cleaned_data["amount"]
        reward_type = cleaned_data["reward_type"]

        if not reward_type == "reward":
            cleaned_data["amount"] = -amount

        return cleaned_data


class TransactionCreateFromPersonForm(
    WithoutFormTagMixin, TransactionCreateEditFormMixin
):
    """
    Creates a transaction for a given person.

    Used for creating a transaction when the person is known
    from the path or query parameters.

    :parameter person: The person to create the transaction for.

    **Request parameters:**

    *   all from :class:`TransactionCreateEditMixin`
    """

    def __init__(self, person: Person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance.person = person


class TransactionCreateBulkForm(TransactionCreateEditFormMixin):
    """
    Creates transactions for a set of persons.

    The created transactions have the same parameters with only persons differing.

    Uses :class:`PersonsFilterForm` for filtering persons.

    **Request parameters:**

    *   all from :class:`TransactionCreateEditMixin`
    *   all from :class:`PersonsFilterForm`
    """

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
        person_filter_form_layout_rows = person_filter_form.helper.layout.fields[  # type: ignore
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
            "reward_type", "amount", "reason", "date_due"
        )

    def clean(self):
        """
        Also cleans the person filter form.
        """

        cleaned_data = super().clean()
        cleaned_data = PersonsFilterForm.clean_with_given_values(cleaned_data)

        return cleaned_data


class TransactionAddTrainingPaymentForm(Form):
    """
    Form for collecting data for creation of a bulk debt transaction for a training.
    Doesn't create the transactions.

    Allows specifying different amounts for different
    number of trainings attended per week.

    Prefills the reason form field with a default value.

    **Request parameters:**

    *   ``reason``
    *   ``date_due``
    *   ``amount_{i}`` - the amount that should be paid
        when he person attends ``i`` occurences per week

    :parameter event: The training to (eventually) create all the transactions for.
    """

    date_due = DateField(
        label=Transaction._meta.get_field("date_due").verbose_name,
        widget=DatePickerWithIcon(),
    )
    reason = CharField(label=Transaction._meta.get_field("reason").verbose_name)

    def __init__(
        self, initial: MutableMapping[str, Any], event: Training, *args, **kwargs
    ):
        initial["reason"] = _("Platba za tréninky - {0}").format(event)
        super().__init__(
            *args,
            initial=initial,
            **kwargs,
        )

        for i in range(event.weekly_occurs_count()):
            self.fields[f"amount_{i}"] = IntegerField(
                label=_("Suma za trénink {0}x týdně").format(i + 1),
                min_value=1,
            )


class Label:
    """
    A crispy layout object for rendering a label.
    """

    def __init__(self, text: Any | None = None):
        self.text = text

    def render(self, form, context, template_pack, extra_context=None, **kwargs):
        """
        Renders a label with class ``col-form-label``
        and content of parameter ``text`` from ``__init__``.
        """

        if self.text is None:
            return ""

        return f"<label class='col-form-label'>{self.text}</label>"


class TransactionCreateBulkConfirmForm(
    WithoutFormTagMixin, InsertRequestIntoSelf, ModelForm
):
    """
    Creates a bulk debt transaction for a training. One :class:`BulkTransaction`
    and multiple :class:`Transaction` instances are created.

    Also notifies the persons about the created transactions.

    **Request parameters:**

    *   ``transactions-{pk}-amount`` - the transaction amount for
        the person with primary key ``pk``
    *   ``transactions-{pk}-date_due`` - the transaction due date for
        the person with primary key ``pk``

    :parameter event: The training to create all the transactions for.
    :parameter reason: The reason for the transactions.

    ``__init__`` parameters are applied to the created bulk transaction
    and are also set the same for all created sub-transactions.
    """

    class Meta:
        model = BulkTransaction
        fields = []

    def __init__(
        self,
        transaction_infos: Iterable[TransactionInfo],
        event: Event = None,
        reason: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.instance.event = event
        self.instance.reason = reason

        self.event = event
        self.reason = reason
        self.transaction_infos = transaction_infos
        self.transactions_and_enrollments: Iterable[tuple[Transaction, Any]]

        self._create_fields(transaction_infos)

        layout_rows = self._create_layout_rows(transaction_infos)
        self._create_form_helper(self.helper, layout_rows)

    def _create_fields(self, transaction_infos: Iterable[TransactionInfo]):
        for transaction_info in transaction_infos:
            field_name_amount = transaction_info.get_amount_field_name()
            field_name_date_due = transaction_info.get_date_due_field_name()

            self.fields[field_name_amount] = IntegerField(
                required=False, initial=transaction_info.amount
            )
            self.fields[field_name_date_due] = DateField(
                required=False,
                initial=transaction_info.date_due,
                widget=DatePickerWithIcon(),
            )

    @staticmethod
    def _create_layout_rows(transaction_infos: Iterable[TransactionInfo]):
        for transaction_info in transaction_infos:
            person = transaction_info.person
            field_name_amount = transaction_info.get_amount_field_name()
            field_name_date_due = transaction_info.get_date_due_field_name()

            yield Row(
                Column(Label(person), css_class="col-md-4"),
                Column(field_name_amount, css_class="col-md-4"),
                Column(field_name_date_due, css_class="col-md-4"),
                css_class="row",
            )

    @staticmethod
    def _create_form_helper(helper: FormHelper, layout_divs: Iterable[Div]):
        helper.form_show_labels = False
        helper.layout = Layout(
            Row(
                Column(Label(), css_class="col-md-4"),
                Column(
                    Label(Transaction._meta.get_field("amount").verbose_name),
                    css_class="col-md-4 text-center",
                ),
                Column(
                    Label(Transaction._meta.get_field("date_due").verbose_name),
                    css_class="col-md-4 text-center",
                ),
                css_class="row",
            ),
            *layout_divs,
        )

    def _clean_impl(self, cleaned_data: MutableMapping[str, Any]):
        for transaction_info in self.transaction_infos:
            person = transaction_info.person

            field_name_amount = transaction_info.get_amount_field_name()
            field_name_date_due = transaction_info.get_date_due_field_name()

            amount = cleaned_data.get(field_name_amount)
            date_due = cleaned_data.get(field_name_date_due)

            if amount is None or amount == 0:
                del cleaned_data[field_name_amount]
                del cleaned_data[field_name_date_due]
                continue

            if date_due is None:
                self.add_error(
                    field_name_date_due, _("Datum splatnosti musí být vyplněno.")
                )
                continue

            if date_due < today():
                self.add_error(
                    field_name_date_due, _("Datum splatnosti nemůže být v minulosti.")
                )
                continue

            yield (
                Transaction(
                    person=person,
                    amount=amount,
                    reason=self.reason,
                    date_due=date_due,
                    event=self.event,
                ),
                transaction_info.enrollment,
            )

    def clean(self):
        cleaned_data = super().clean()

        self.transactions_and_enrollments = list(self._clean_impl(cleaned_data))

        return cleaned_data

    def save(self, commit: bool = True):
        """
        Sends an email to each person a transaction was created for.
        """

        bulk_transaction = super().save(False)

        if commit:
            bulk_transaction.save()

        for transaction, enrollment in self.transactions_and_enrollments:
            transaction.bulk_transaction = bulk_transaction

            if commit:
                transaction.save()

            if enrollment:
                enrollment.transactions.add(transaction)
                self._send_new_transaction_with_enrollment_email(
                    enrollment, transaction
                )
            else:
                self._send_new_transaction_with_reason_email(self.reason, transaction)

        return bulk_transaction

    def _send_new_transaction_with_enrollment_email(
        self, enrollment: ParticipantEnrollment, transaction: Transaction
    ):
        payment_html = "<br><br>" + payment_email_html(transaction, self.request)
        send_notification_email(
            _("Nová transakce k zaplacení"),
            _("U události {0} byla vytvořena" "nová transakce k zaplacení.").format(
                enrollment.event
            )
            + payment_html,
            [enrollment.person],
        )

    def _send_new_transaction_with_reason_email(
        self, reason: str, transaction: Transaction
    ):
        payment_html = "<br><br>" + payment_email_html(transaction, self.request)
        send_notification_email(
            _("Nová transakce k zaplacení"),
            _("Byla pro vás vytvořena nová transakce s popisem {0}").format(reason)
            + payment_html,
            [transaction.person],
        )


class TransactionCreateEditPersonSelectFormMixin(
    WithoutFormTagMixin, TransactionCreateEditFormMixin
):
    """
    A mixin for creating or editing a transaction.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.include_media = False


class TransactionCreateForm(TransactionCreateEditPersonSelectFormMixin):
    """
    Creates a transaction for a given person.

    The person is selected in the form and sent in the request body
    in contrast to :class:`TransactionCreateFromPersonForm`.

    **Request parameters:**

    *   ``person``
    *   ``amount``
    *   ``reason``
    *   ``date_due``
    *   ``reward_type``
    """

    class Meta(TransactionCreateEditFormMixin.Meta):
        fields = ["person"] + TransactionCreateEditFormMixin.Meta.fields
        widgets = TransactionCreateEditFormMixin.Meta.widgets
        widgets["person"] = PersonSelectWidget()


class TransactionEditForm(TransactionCreateEditPersonSelectFormMixin):
    """
    Edits a transaction.

    **Request parameters:**

    *   ``amount``
    *   ``reason``
    *   ``date_due``
    *   ``reward_type``
    """

    def __init__(
        self, initial: MutableMapping[str, Any], instance: Transaction, *args, **kwargs
    ):
        initial["reward_type"] = "reward" if instance.amount > 0 else "debt"
        instance.amount = abs(instance.amount)

        super().__init__(*args, initial=initial, instance=instance, **kwargs)


class TransactionFilterForm(Form):
    """
    Filters transactions based on simple predicates.

    Use :func:`process_filter` to get the filtered transactions.

    **Request parameters:**

    *   ``person_name``
    *   ``reason``
    *   ``transaction_type``
    *   ``is_settled``
    *   ``amount_from``
    *   ``amount_to``
    *   ``date_due_from``
    *   ``date_due_to``
    *   ``bulk_transaction``
    """

    person_name = CharField(label=_("Jméno osoby obsahuje"), required=False)
    reason = CharField(label=_("Popis obsahuje"), required=False)
    transaction_type = ChoiceField(
        label=_("Typ transakce"),
        required=False,
        choices=[("", "---------")] + [("reward", "Odměna"), ("debt", "Dluh")],
    )
    is_settled = ChoiceField(
        label=_("Transakce zaplacena"),
        required=False,
        choices=[("", "---------")] + [("paid", "Ano"), ("not paid", "Ne")],
    )
    amount_from = IntegerField(label=_("Suma od"), required=False, min_value=1)
    amount_to = IntegerField(label=_("Suma do"), required=False, min_value=1)
    date_due_from = DateField(
        label=_("Datum splatnosti od"), required=False, widget=DatePickerWithIcon()
    )
    date_due_to = DateField(
        label=_("Datum splatnosti do"), required=False, widget=DatePickerWithIcon()
    )
    bulk_transaction = ModelChoiceField(
        label=_("Hromadná transakce"),
        queryset=BulkTransaction.objects.all(),
        required=False,
        widget=Select2Widget,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = self._create_form_helper()

    @staticmethod
    def _create_form_helper():
        helper = FormHelper()

        helper.form_method = "GET"
        helper.form_id = "transactions-filter-form"
        helper.include_media = False
        helper.layout = Layout(
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
                        HTML(
                            "<a href='.' class='btn btn-secondary ml-1 float-right'>Zrušit</a>"
                        ),
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

        return helper

    def clean(self):
        cleaned_data = super().clean()

        amount_from = cleaned_data.get("amount_from")
        amount_to = cleaned_data.get("amount_to")
        date_due_from = cleaned_data.get("date_due_from")
        date_due_to = cleaned_data.get("date_due_to")

        if (
            amount_from is not None
            and amount_to is not None
            and amount_from > amount_to
        ):
            raise ValidationError(_("Suma od musí být menší nebo rovna sumě do."))

        if (
            date_due_from is not None
            and date_due_to is not None
            and date_due_from > date_due_to
        ):
            raise ValidationError(
                _("Datum splatnosti od musí být menší nebo roven datumu splatnosti do.")
            )

    def process_filter(self) -> QuerySet[Transaction]:
        """
        Processes the filter and returns the matching transactions.

        Returns all transactions if the form is invalid.
        """
        transactions = Transaction.objects.all()

        return filter_queryset(
            transactions,
            self.cleaned_data if self.is_valid() else None,
            TransactionFilter,
        )


class TransactionAccountingExportPeriodForm(Form):
    """
    Selection form for which period the accounting basis should be exported.
    """

    year = IntegerField(label=_("Rok"), min_value=2000, max_value=today().year)
    month = ChoiceField(
        label=_("Měsíc"),
        required=True,
        choices=[("", "---------")]
        + [(i, month) for i, month in enumerate(MONTH_NAMES, start=1)],
    )
    type = ChoiceField(
        label=_("Typ exportu"),
        required=True,
        choices=[
            ("", "---------"),
            ("vyplaty", "Výplaty v csv"),
            ("pohledavky", "Pohledávky v Pohoda XML"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if today().month != 1:
            self.initial["year"] = today().year
            self.initial["month"] = today().month - 1
        else:
            self.initial["year"] = today().year - 1
            self.initial["month"] = 12
