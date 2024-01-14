from collections.abc import Iterable, Mapping
from itertools import chain
from typing import Any

from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import SuspiciousOperation
from django.db.models import Q, Sum
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from events.permissions import EventManagePermissionMixin
from events.views import (
    InsertEventIntoModelFormKwargsMixin,
    RedirectToEventDetailOnSuccessMixin,
)
from persons.models import Person, get_active_user
from persons.utils import PersonsFilter
from persons.views import PersonPermissionMixin
from trainings.models import Training
from users.permissions import LoginRequiredMixin
from vzs.mixins import InsertRequestIntoModelFormKwargsMixin
from vzs.settings import FIO_ACCOUNT_PRETTY
from vzs.utils import export_queryset_csv, filter_queryset, reverse_with_get_params
from .forms import (
    TransactionAccountingExportPeriodForm,
    TransactionAddTrainingPaymentForm,
    TransactionCreateBulkConfirmForm,
    TransactionCreateBulkForm,
    TransactionCreateForm,
    TransactionCreateFromPersonForm,
    TransactionEditForm,
    TransactionFilterForm,
)
from .models import BulkTransaction, Transaction
from .permissions import (
    TransactionDisableEditSettledPermissionMixin,
    TransactionEditPermissionMixin,
)
from .utils import (
    TransactionInfo,
    export_debts_to_xml,
    export_rewards_to_csv,
    send_email_transaction,
)


class TransactionCreateView(TransactionEditPermissionMixin, CreateView):
    """
    Creates a new :class:`transactions.models.Transaction`.

    Allows selecting a person from a list of all persons.

    **Success redirection view**: :class:`transactions.views.TransactionIndexView`

    **Permissions**:

    Users with the ``users.transakce`` permission.
    """

    form_class = TransactionCreateForm
    """:meta private:"""

    model = Transaction
    """:meta private:"""

    success_url = reverse_lazy("transactions:index")
    """:meta private:"""

    template_name = "transactions/create.html"
    """:meta private:"""


class TransactionCreateFromPersonView(
    TransactionEditPermissionMixin, SuccessMessageMixin, CreateView
):
    """
    A view for creating a new transaction.

    The person comes from the path parameters.

    **Success redirection view**: :class:`TransactionListView`
    of the person the transaction was created for

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Path parameters:**

    *   ``person`` - ID of the person to create the transaction for
    """

    form_class = TransactionCreateFromPersonForm
    """:meta private:"""

    model = Transaction
    """:meta private:"""

    template_name = "transactions/create_from_person.html"
    """:meta private:"""

    success_message = _("Transakce byla přidána")

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """:meta private:"""

        self.person = get_object_or_404(Person, pk=self.kwargs["person"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        *   ``person`` - the :class:`persons.models.Person` from the path parameters
        """

        kwargs.setdefault("person", self.person)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs.setdefault("person", self.person)

        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        send_email_transaction(self.object)

        return response


class TransactionListMixin(TransactionEditPermissionMixin, DetailView):
    """
    A mixin that provides context data used by views
    that list transactions for a certain person.

    **Path parameters:**

    *   ``pk`` - ID of the person to list transactions for
    """

    model = Person

    def get_context_data(self, **kwargs):
        """
        *   ``transactions_debt`` - a queryset of person's debt transactions
        *   ``transactions_reward`` - a queryset of person's reward transactions
        *   ``current_debt`` - the person's current total debt
        *   ``due_reward`` - the person's total due reward
        """

        person = self.object
        transactions: QuerySet[Transaction] = person.transactions

        transactions_debt = transactions.filter(Transaction.Q_debt)
        transactions_reward = transactions.filter(Transaction.Q_reward)

        transactions_due = transactions.filter(fio_transaction__isnull=True)
        transactions_current_debt = transactions_due.filter(Transaction.Q_debt)
        transactions_due_reward = transactions_due.filter(Transaction.Q_reward)

        current_debt = (
            transactions_current_debt.aggregate(result=Sum("amount"))["result"] or 0
        )
        due_reward = (
            transactions_due_reward.aggregate(result=Sum("amount"))["result"] or 0
        )

        kwargs.setdefault("transactions_debt", transactions_debt)
        kwargs.setdefault("transactions_reward", transactions_reward)
        kwargs.setdefault("current_debt", current_debt)
        kwargs.setdefault("due_reward", due_reward)

        return super().get_context_data(**kwargs)


class TransactionListView(TransactionListMixin):
    """
    A view that displays a list of transactions for a certain person.

    **Permissions**:

    *   users with the ``users.transakce`` permission
    *   users that manage the transaction's person's membership type

    **Path parameters:**

    *   ``pk`` - ID of the person to list transactions for
    """

    template_name = "transactions/list.html"
    """:meta private:"""

    def get_queryset(self):
        """:meta private:"""

        if get_active_user(self.request.active_person).has_perm("transakce"):
            return super().get_queryset()
        else:
            return PersonPermissionMixin.get_queryset_by_permission(self.request.user)


class TransactionQRView(LoginRequiredMixin, DetailView):
    """
    Display the QR code for a given transaction.

    See :func:`get_queryset` for more information.

    **Permissions**:

    *   users with the ``users.transakce`` permission
    *   users that manage the transaction's person's membership type
    *   the user to whom the transaction belongs

    **Path parameters:**

    *   ``pk`` - ID of the transaction to display the QR code for
    """

    template_name = "transactions/QR.html"

    def get_context_data(self, **kwargs):
        """
        *   ``person`` - the person associated with the transaction
        """

        kwargs.setdefault("person", self.object.person)
        kwargs.setdefault("account", FIO_ACCOUNT_PRETTY)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """:meta private:"""

        active_person = self.request.active_person
        active_user = get_active_user(active_person)

        queryset = Transaction.objects.filter(
            Q(fio_transaction__isnull=True) & Transaction.Q_debt
        )
        if not active_user.has_perm("transakce"):
            queryset = queryset.filter(
                Q(person=active_person)
                | Q(
                    person__in=PersonPermissionMixin.get_queryset_by_permission(
                        active_user
                    )
                )
            )

        return queryset


class TransactionEditMixin(TransactionEditPermissionMixin, UpdateView):
    """
    A mixin used by views that edit transactions.

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Path parameters:**

    *   ``pk`` - ID of the transaction to edit
    """

    form_class = TransactionEditForm
    """:meta private:"""

    model = Transaction
    """:meta private:"""

    template_name = "transactions/edit.html"
    """:meta private:"""

    def get_context_data(self, **kwargs):
        """
        *   ``person`` - the person associated with the edited transaction
        """

        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_form(self):
        """:meta private:"""

        # get_success_url is run after object update so we need to save the data
        # we will need later
        self.old_person = self.object.person
        return super().get_form()


class TransactionEditFromPersonView(
    TransactionDisableEditSettledPermissionMixin, TransactionEditMixin
):
    """
    Edits a transaction.

    **Success redirection view**: :class:`TransactionListView`
    of the transaction's original associated person

    **Path parameters:**

    *   ``pk`` - ID of the transaction to edit
    """

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:transaction-list", kwargs={"pk": self.old_person.pk})


class TransactionEditView(
    TransactionDisableEditSettledPermissionMixin, TransactionEditMixin
):
    """
    Edits a transaction.

    **Success redirection view**: :class:`TransactionIndexView`

    **Path parameters:**

    *   ``pk`` - ID of the transaction to edit
    """

    success_url = reverse_lazy("transactions:index")
    """:meta private:"""


class TransactionDeleteView(TransactionEditPermissionMixin, DeleteView):
    """
    Deletes a transaction.

    **Success redirection view**: :class:`TransactionListView`
    of the transaction's associated person

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Path parameters:**

    *   ``pk`` - ID of the transaction to delete
    """

    model = Transaction
    """:meta private:"""

    template_name = "transactions/delete.html"
    """:meta private:"""

    def form_valid(self, form):
        """:meta private:"""

        # redirection is done after object deletion so we need to save the data
        # we will need later
        self.person = self.object.person
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        *   ``person`` - the person associated with the edited transaction
        """

        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})


class BulkTransactionIndexView(TransactionEditPermissionMixin, ListView):
    """
    Displays a list of bulk transactions

    Allow direct deletion using modals.

    **Permissions**:

    Users with the ``transakce`` permission.
    """

    context_object_name = "bulk_transactions"
    """:meta private:"""

    model = BulkTransaction
    """:meta private:"""

    template_name = "transactions/bulk_transactions.html"
    """:meta private:"""


class TransactionIndexView(TransactionEditPermissionMixin, ListView):
    """
    Displays a list of all transactions

    Allow direct deletion using modals.

    Filters regular transactions using :class:`TransactionFilterForm`.

    **Permissions**:

    Users with the ``transakce`` permission.

    **Query parameters:**

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

    context_object_name = "transactions"
    """:meta private:"""

    model = Transaction
    """:meta private:"""

    template_name = "transactions/index.html"
    """:meta private:"""

    def get_context_data(self, **kwargs):
        """
        *   ``bulk_transactions`` - queryset of all bulk transactions
        *   ``filtered_get`` - url encoded GET parameters
            that were used to filter the transactions
        *   ``form`` - the filter form
        *   ``transactions`` - queryset of filtered transactions
        """

        kwargs.setdefault("form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        """:meta private:"""

        self.filter_form = TransactionFilterForm(self.request.GET)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Orders the transactions by due date.
        """

        return self.filter_form.process_filter().order_by("-pk")


class TransactionCreateBulkView(TransactionEditPermissionMixin, FormView):
    """
    A view for creating bulk transactions for a set of persons.
    Doesn't create the transactions, only redirects to the confirmation view.

    **Success redirection view**: :class:`TransactionCreateBulkConfirmView`. Passes it
    the request body parameters as query parameters.

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Request body parameters:**

    *   ``amount``
    *   ``reason``
    *   ``date_due``
    *   ``is_reward``
    *   ``name``
    *   ``email``
    *   ``qualifications``
    *   ``permissions``
    *   ``equipments``
    *   ``person_type``
    *   ``age_from``
    *   ``age_to``

    **Path parameters:**

    *   ``is_already_filtered`` - whether the request body parameters
        contain person filter parameters
    """

    form_class = TransactionCreateBulkForm
    """:meta private:"""

    template_name = "transactions/create_bulk.html"
    """:meta private:"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirm_get_params: Mapping[str, Any]
        self.already_filtered_get_params = None

    def dispatch(
        self, request: HttpRequest, is_already_filtered: bool = False, *args, **kwargs
    ):
        """:meta private:"""

        if is_already_filtered:
            self.already_filtered_get_params = request.GET

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        *   ``is_already_filtered`` - whether the request body parameters
            contain person filter parameters
        """

        kwargs.setdefault(
            "is_already_filtered", self.already_filtered_get_params is not None
        )

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        """:meta private:"""

        return reverse_with_get_params(
            "transactions:add-bulk-confirm", get=self.confirm_get_params
        )

    def form_valid(self, form: Form):
        """:meta private:"""

        if self.already_filtered_get_params is None:
            self.confirm_get_params = {
                key: value
                for key, value in form.cleaned_data.items()
                if value not in {None, ""} and key != "csrfmiddlewaretoken"
            }
        else:
            self.confirm_get_params = {
                "amount": form.cleaned_data["amount"],
                "reason": form.cleaned_data["reason"],
                "date_due": form.cleaned_data["date_due"],
                **self.already_filtered_get_params.dict(),
            }

        return super().form_valid(form)


class TransactionAddTrainingPaymentView(
    EventManagePermissionMixin, InsertEventIntoModelFormKwargsMixin, FormView
):
    """
    A view for creating a bulk transaction as a payment for a training.
    Doesn't create the transactions, only redirects to the confirmation view.

    **Success redirection view**: :class:`TransactionCreateTrainingBulkConfirmView`.
    Passes it the request body parameters as query parameters.

    **Permissions**:

    Users that manage the training for which the transactions are created.

    **Request body parameters:**

    *   ``reason``
    *   ``date_due``
    *   ``amount_{i}`` - the amount that should be paid
        when he person attends ``i`` occurences per week

    **Path parameters:**

    *   ``event_id`` - ID of the training to create the bulk transaction for
    """

    event_id_key = "event_id"
    """:meta private:"""

    form_class = TransactionAddTrainingPaymentForm
    """:meta private:"""

    template_name = "transactions/create_training_transaction.html"
    """:meta private:"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirm_get_params: Mapping[str, Any]

    def get_success_url(self):
        """:meta private:"""

        return reverse_with_get_params(
            "trainings:add-transaction-confirm",
            kwargs={"event_id": self.event.id},
            get=self.confirm_get_params,
        )

    def form_valid(self, form: Form):
        """:meta private:"""

        self.confirm_get_params = {
            "reason": form.cleaned_data["reason"],
            "date_due": form.cleaned_data["date_due"],
        }

        for i in range(self.event.weekly_occurs_count()):
            self.confirm_get_params[f"amount_{i}"] = form.cleaned_data[f"amount_{i}"]

        return super().form_valid(form)


class TransactionCreateBulkConfirmMixin(
    SuccessMessageMixin,
    InsertRequestIntoModelFormKwargsMixin,
    TransactionEditPermissionMixin,
    CreateView,
):
    """
    A mixin for creating bulk transactions.

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Query parameters:**

    *   ``reason`` - the reason for all the transactions
    """

    form_class = TransactionCreateBulkConfirmForm

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """:meta private:"""

        query_parameters = self.request.GET
        required_parameters = {"reason", *self.additional_required_parameters()}

        if not required_parameters.issubset(query_parameters.keys()):
            raise SuspiciousOperation("Missing parameters")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        query_parameters = self.request.GET

        transaction_infos = list(self.create_transaction_infos(query_parameters))
        kwargs.setdefault("transaction_infos", transaction_infos)
        kwargs.setdefault("reason", query_parameters.get("reason", ""))

        return kwargs

    def create_transaction_infos(
        self, query_parameters: Mapping[str, Any]
    ) -> Iterable[TransactionInfo]:
        """
        Creates transaction infos based on query parameters.
        """

        raise NotImplementedError

    def additional_required_parameters(self) -> Iterable[str]:
        """
        Returns a list of additional required query parameters.
        """

        raise NotImplementedError


class TransactionCreateSameAmountBulkConfirmView(TransactionCreateBulkConfirmMixin):
    """
    Creates a bulk transaction with the same amount for all persons.

    **Success redirection view**: :class:`TransactionIndexView`

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Query parameters:**

    *   ``reason`` - the reason for all the transactions
    *   all from :class:`persons.forms.PersonFilterForm`
    *   ``amount`` - the amount of all the transactions
    *   ``date_due`` - the due date of all the transactions
    """

    success_message = _("Hromadná transakce byla přidána")
    """:meta private:"""

    success_url = reverse_lazy("transactions:index")
    """:meta private:"""

    template_name = "transactions/create_bulk_confirm.html"
    """:meta private:"""

    def create_transaction_infos(
        self, query_parameters: Mapping[str, Any]
    ) -> Iterable[TransactionInfo]:
        """
        Filters the persons and creates transaction infos accordingly.
        """

        selected_persons = filter_queryset(
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
            query_parameters,
            PersonsFilter,
        )

        for person in selected_persons:
            yield TransactionInfo(
                person=person,
                amount=query_parameters["amount"],
                date_due=query_parameters["date_due"],
            )

    def additional_required_parameters(self) -> Iterable[str]:
        return ["amount", "date_due"]


class TransactionCreateTrainingBulkConfirmView(
    EventManagePermissionMixin,
    RedirectToEventDetailOnSuccessMixin,
    TransactionCreateBulkConfirmMixin,
):
    """
    Creates a bulk transaction for a training.

    **Success redirection view**: :class:`trainings.views.TrainingDetailView`
    of the training the transactions were created for

    **Permissions**:

    Users that manage the training for which the transactions are created.

    **Query parameters:**

    *   ``reason`` - the reason for all the transactions
    *   ``date_due`` - the due date of all the transactions
    *   ``amount_{i}`` - the amount for person to pay
        if they are enrolled in ``i`` training occurences per week

    **Path parameters:**

    *   ``event_id`` - ID of the training to create the bulk transaction for
    """

    event_id_key = "event_id"
    """:meta private:"""

    success_message = _("Hromadná transakce byla přidána")
    """:meta private:"""

    template_name = "transactions/create_bulk_confirm.html"
    """:meta private:"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event: Training

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.event = get_object_or_404(Training, pk=self.kwargs["event_id"])

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs.setdefault("event", self.event)
        return kwargs

    def create_transaction_infos(
        self, query_parameters: Mapping[str, Any]
    ) -> Iterable[TransactionInfo]:
        """
        Generates transaction infos for all persons enrolled in the training.
        """

        approved_enrollments = self.event.approved_enrollments()

        for enrollment in approved_enrollments:
            person = enrollment.person

            repetition_per_week = enrollment.weekdays.count()
            amount = -int(query_parameters[f"amount_{repetition_per_week - 1}"])

            yield TransactionInfo(
                person=person,
                amount=amount,
                date_due=query_parameters["date_due"],
                enrollment=enrollment,
            )

    def additional_required_parameters(self) -> Iterable[str]:
        return chain(
            ["date_due"],
            [f"amount_{i}" for i in range(self.event.weekly_occurs_count())],
        )


class TransactionExportView(TransactionEditPermissionMixin, View):
    """
    A view for exporting transaction info into a CSV file.

    Filters using :class:`TransactionFilterForm`.

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Query parameters:**

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

    http_method_names = ["get"]
    """:meta private:"""

    def get(self, request: HttpRequest, *args, **kwargs):
        """:meta private:"""

        filter_form = TransactionFilterForm(request.GET)

        return export_queryset_csv("vzs_transakce_export", filter_form.process_filter())


class MyTransactionsView(LoginRequiredMixin, TransactionListMixin):
    """
    Displays a list of transactions for the active person.

    **Permissions**:

    Logged in users.
    """

    template_name = "transactions/my_transactions.html"
    """:meta private:"""

    def get_object(self, queryset=None):
        """:meta private:"""

        return self.request.active_person


class BulkTransactionDeleteView(
    TransactionEditPermissionMixin, SuccessMessageMixin, DeleteView
):
    """
    Deletes a bulk transaction. This means deleting
    the :class:`BulkTransaction` instance
    and also all the associated :class:`Transaction` instances.

    **Permissions**:

    Users with the ``users.transakce`` permission.

    **Path parameters:**

    *   ``pk`` - ID of the bulk transaction to delete
    """

    context_object_name = "bulk_transaction"
    """:meta private:"""

    model = BulkTransaction
    """:meta private:"""

    template_name = "transactions/delete_bulk.html"
    """:meta private:"""

    success_url = reverse_lazy("transactions:index")

    success_message = _("Hromadná transakce byla smazána")

    def form_valid(self, form):
        self.object.transaction_set.all().delete()

        return super().form_valid(form)


class TransactionAccountingExportView(TransactionEditPermissionMixin, FormView):
    """
    Enables exporting transactions as an accounting basis. The rewards
    are exported as a CSV file and the debts as an XML file, which can be imported
    to the Pohoda software.

    **Permissions**:

    Users with the ``transakce`` permission.
    """

    form_class = TransactionAccountingExportPeriodForm
    """:meta private:"""

    template_name = "transactions/accounting_export.html"
    """:meta private:"""

    success_url = reverse_lazy("transactions:accounting-export")
    """:meta private:"""

    def form_valid(self, form):
        _ = super().form_valid(form)

        export_type = form.cleaned_data["type"]

        if export_type == "pohledavky":
            return export_debts_to_xml(
                form.cleaned_data["year"], form.cleaned_data["month"]
            )
        elif export_type == "vyplaty":
            return export_rewards_to_csv(
                form.cleaned_data["year"], form.cleaned_data["month"]
            )
        else:
            raise SuspiciousOperation("Missing parameters")
