from collections.abc import Iterable, Mapping
from itertools import chain
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Sum
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.permissions import EventManagePermissionMixin
from events.views import (
    InsertEventIntoModelFormKwargsMixin,
    RedirectToEventDetailOnSuccessMixin,
)
from persons.models import Person
from persons.utils import parse_persons_filter_queryset
from persons.views import PersonPermissionMixin
from trainings.models import Training
from vzs.mixin_extensions import InsertRequestIntoModelFormKwargsMixin
from vzs.utils import export_queryset_csv, reverse_with_get_params

from .forms import (
    TransactionAddTrainingPaymentForm,
    TransactionCreateBulkConfirmForm,
    TransactionCreateBulkForm,
    TransactionCreateForm,
    TransactionCreateFromPersonForm,
    TransactionEditForm,
    TransactionFilterForm,
)
from .models import Transaction
from .utils import TransactionInfo, send_email_transactions


class TransactionEditPermissionMixin(PermissionRequiredMixin):
    """
    Permission mixin permitting only users
    with the ``transactions.spravce_transakci`` permission.

    Used for views that manage transactions.
    """

    permission_required = "transactions.spravce_transakci"


class TransactionCreateView(TransactionEditPermissionMixin, generic.edit.CreateView):
    """
    A view for creating a new transaction.

    Allows selecting a person from a list of all persons.
    """

    model = Transaction
    form_class = TransactionCreateForm
    template_name = "transactions/create.html"
    success_url = reverse_lazy("transactions:index")


class TransactionCreateFromPersonView(
    TransactionEditPermissionMixin, generic.edit.CreateView
):
    """
    A view for creating a new transaction.

    The person comes from the path parameters.

    **Path parameters:**

    *   ``person`` - ID of the person to create the transaction for
    """

    model = Transaction
    form_class = TransactionCreateFromPersonForm
    template_name = "transactions/create_from_person.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.person = get_object_or_404(Person, pk=self.kwargs["person"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.person)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs.setdefault("person", self.person)

        return kwargs


class TransactionListMixin(generic.detail.DetailView):
    """
    A mixin that provides context data used by views
    that list transactions for a certain person.

    **Path parameters:**

    *   ``pk`` - ID of the person to list transactions for
    """

    model = Person

    def get_context_data(self, **kwargs):
        """
        **Variables provided**:

        *   ``transactions_debt``: a queryset of person's debt transactions
        *   ``transactions_reward``: a queryset of person's reward transactions
        *   ``current_debt``: the person's current total debt
        *   ``due_reward``: the person's total due reward
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

    **Path parameters:**

    *   all from :class:`TransactionListMixin`
    """

    template_name = "transactions/list.html"

    def get_queryset(self):
        if self.request.user.has_perm("transactions.spravce_transakci"):
            return super().get_queryset()
        else:
            return PersonPermissionMixin.get_queryset_by_permission(self.request.user)


class TransactionQRView(generic.detail.DetailView):
    """
    Display the QR code for a given transaction.

    **Path parameters:**

    *   ``pk`` - ID of the transaction to display the QR code for

    See :func:`get_queryset` for more information.
    """

    template_name = "transactions/QR.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """
        Throws 404 if the transaction is already settled or is a reward.

        If the user is not a transaction manager, throws 404 if the transaction
        does not belong to them.
        """

        queryset = Transaction.objects.filter(
            Q(fio_transaction__isnull=True) & Transaction.Q_debt
        )
        if not self.request.user.has_perm("transactions.spravce_transakci"):
            queryset = queryset.filter(
                person__in=PersonPermissionMixin.get_queryset_by_permission(
                    self.request.user
                )
            )

        return queryset


class TransactionEditMixin(TransactionEditPermissionMixin, generic.edit.UpdateView):
    """
    A mixin used by views that edit transactions.

    **Path parameters:**

    *   ``pk`` - ID of the transaction to edit
    """

    model = Transaction
    form_class = TransactionEditForm
    template_name = "transactions/edit.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_form(self):
        """
        Sets ``self.old_person`` to the person
        the transaction belongs to at the beginning.

        Used when the transaction's associated person is changed
        but the deriving view wants to access the original person.
        """

        # get_success_url is run after object update so we need to save the data
        # we will need later
        self.old_person = self.object.person
        return super().get_form()


class TransactionEditFromPersonView(TransactionEditMixin):
    """
    Edits a transaction.

    **Path parameters:**

    *   all from :class:`TransactionEditMixin`
    """

    def get_success_url(self):
        """
        Redirects to the original transaction's person's transaction list view
        regardless whether the person was changed or not.
        """

        return reverse("persons:transaction-list", kwargs={"pk": self.old_person.pk})


class TransactionEditView(TransactionEditMixin):
    """
    Edits a transaction.

    Redirects to the transactions index view.

    **Path parameters:**

    *   all from :class:`TransactionEditMixin`
    """

    success_url = reverse_lazy("transactions:index")


class TransactionDeleteView(TransactionEditPermissionMixin, generic.edit.DeleteView):
    """
    Deletes a transaction.

    **Path parameters:**

    *   ``pk`` - ID of the transaction to delete
    """

    model = Transaction
    template_name = "transactions/delete.html"

    def form_valid(self, form):
        # success_message is sent after object deletion so we need to save the data
        # we will need later
        self.person = self.object.person
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        """
        Redirects to the associated person's transaction list view.
        """

        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})


class TransactionIndexView(TransactionEditPermissionMixin, generic.list.ListView):
    """
    Displays a list of all transactions.

    Filters using :class:`TransactionFilterForm`.

    **Query parameters:**

    *   all from :class:`TransactionFilterForm`
    """

    model = Transaction
    template_name = "transactions/index.html"
    context_object_name = "transactions"

    def get_context_data(self, **kwargs):
        """
        **Variables provided**:

        *   ``form``: the filter form
        *   ``filtered_get``: url encoded GET parameters
            that were used to filter the transactions
        """

        kwargs.setdefault("form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        self.filter_form = TransactionFilterForm(self.request.GET)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Applies the filter and orders the transactions by due date.
        """

        return self.filter_form.process_filter().order_by("date_due")


class TransactionCreateBulkView(TransactionEditPermissionMixin, generic.edit.FormView):
    """
    A view for creating bulk transactions for a set of persons.
    Doesn't create the transactions, only redirects to the confirmation view.

    **Request body parameters:**

    *   all from :class:`TransactionCreateBulkForm`

    **Path parameters:**

    *   ``is_already_filtered`` - whether the request body parameters
        contain filter parameters
    """

    template_name = "transactions/create_bulk.html"
    form_class = TransactionCreateBulkForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirm_get_params: Mapping[str, Any]
        self.already_filtered_get_params = None

    def dispatch(
        self, request: HttpRequest, is_already_filtered: bool = False, *args, **kwargs
    ):
        if is_already_filtered:
            self.already_filtered_get_params = request.GET

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.already_filtered_get_params is not None:
            kwargs.setdefault("is_already_filtered", True)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        """
        Redirects to the confirmation view. Passes it
        the :class:`TransactionCreateBulkForm`'s cleaned data as query parameters.
        """

        return reverse_with_get_params(
            "transactions:add-bulk-confirm", get=self.confirm_get_params
        )

    def form_valid(self, form: Form):
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
    EventManagePermissionMixin, InsertEventIntoModelFormKwargsMixin, generic.FormView
):
    """
    A view for creating a bulk transaction as a payment for a training.
    Doesn't create the transactions, only redirects to the confirmation view.
    """

    template_name = "transactions/create_training_transaction.html"
    form_class = TransactionAddTrainingPaymentForm
    event_id_key = "event_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirm_get_params: Mapping[str, Any]

    def get_success_url(self):
        """
        Redirects to the confirmation view. Passes it
        the :class:`TransactionAddTrainingPaymentForm`'s cleaned data
        as query parameters.
        """

        return reverse_with_get_params(
            "trainings:add-transaction-confirm",
            kwargs={"event_id": self.event.id},
            get=self.confirm_get_params,
        )

    def form_valid(self, form: Form):
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
    generic.edit.CreateView,
):
    """
    A mixin for creating bulk transactions.

    **Query parameters:**

    *   ``reason`` - the reason for all the transactions
    """

    form_class = TransactionCreateBulkConfirmForm

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        query_parameters = self.request.GET
        required_parameters = chain(["reason"], self.additional_required_parameters())

        if not set(query_parameters.keys()).issubset(required_parameters):
            return HttpResponseBadRequest(b"Missing parameters")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
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

    **Query parameters:**

    *   all from :class:`TransactionCreateBulkConfirmMixin`
    *   all from :class:`persons.forms.PersonFilterForm`
    *   ``amount`` - the amount of all the transactions
    *   ``date_due`` - the due date of all the transactions
    """

    template_name = "transactions/create_bulk_confirm.html"
    success_url = reverse_lazy("transactions:index")
    success_message = _("Hromadná transakce byla přidána")

    def create_transaction_infos(
        self, query_parameters: Mapping[str, Any]
    ) -> Iterable[TransactionInfo]:
        """
        Filters the persons and creates transaction infos accordingly.
        """

        selected_persons = parse_persons_filter_queryset(
            query_parameters,
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
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

    **Query parameters:**

    *   all from :class:`TransactionCreateBulkConfirmMixin`
    *   ``date_due`` - the due date of all the transactions
    *   ``amount_{i}`` - the amount for person to pay
        if they are enrolled in ``i`` training occurences per week

    **Path parameters:**

    *   ``event_id`` - ID of the training to create the bulk transaction for
    """

    template_name = "transactions/create_bulk_confirm.html"
    success_message = _("Hromadná transakce byla přidána")
    event_id_key = "event_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event: Training

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Training, pk=self.kwargs["event_id"])

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
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


class TransactionExportView(TransactionEditPermissionMixin, generic.base.View):
    """
    A view for exporting transaction info into a CSV file.

    Filters using :class:`TransactionFilterForm`.
    """

    http_method_names = ["get"]

    def get(self, request: HttpRequest, *args, **kwargs):
        filter_form = TransactionFilterForm(request.GET)

        return export_queryset_csv("vzs_transakce_export", filter_form.process_filter())


class TransactionSendEmailView(generic.View):
    """
    Sends an email with transaction info for a set of transactions.

    Filters using :class:`TransactionFilterForm`.
    """

    http_method_names = ["get"]

    def get(self, request: HttpRequest, *args, **kwargs):
        filter_form = TransactionFilterForm(request.GET)

        send_email_transactions(filter_form.process_filter())

        return HttpResponseRedirect(
            f"{reverse('transactions:index')}?{request.GET.urlencode()}"
        )


class MyTransactionsView(LoginRequiredMixin, TransactionListMixin):
    """
    Displays a list of transactions for the active person.
    """

    template_name = "transactions/my_transactions.html"

    def get_object(self, queryset=None):
        return self.request.active_person
