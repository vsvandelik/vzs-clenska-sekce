from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from persons.models import Person
from persons.views import PersonPermissionMixin
from .forms import (
    TransactionEditForm,
    TransactionCreateForm,
    TransactionCreateFromPersonForm,
    TransactionFilterForm,
)
from .models import Transaction
from .utils import parse_transactions_filter_queryset


class TransactionEditPermissionMixin(PermissionRequiredMixin):
    permission_required = "transactions.spravce_transakci"


class TransactionCreateView(TransactionEditPermissionMixin, generic.edit.CreateView):
    model = Transaction
    form_class = TransactionCreateForm
    template_name = "transactions/create.html"
    success_url = reverse_lazy("transactions:index")


class TransactionCreateFromPersonView(
    TransactionEditPermissionMixin, generic.edit.CreateView
):
    model = Transaction
    form_class = TransactionCreateFromPersonForm
    template_name = "transactions/create_from_person.html"

    def dispatch(self, request, *args, **kwargs):
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
    model = Person

    def get_context_data(self, **kwargs):
        person = self.object
        transactions = person.transactions

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
    template_name = "transactions/list.html"

    def get_context_data(self, **kwargs):
        person = self.object
        transactions = person.transactions

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

    def get_queryset(self):
        if self.request.user.has_perm("transactions.spravce_transakci"):
            return super().get_queryset()
        else:
            return PersonPermissionMixin.get_queryset_by_permission(self.request.user)


class TransactionQRView(generic.detail.DetailView):
    template_name = "transactions/QR.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            Q(fio_transaction__isnull=True) & Q(amount__lt=0)
        )
        if not self.request.user.has_perm("transactions.spravce_transakci"):
            queryset = queryset.filter(
                person__in=PersonPermissionMixin.get_queryset_by_permission(
                    self.request.user
                )
            )

        return queryset


class TransactionEditMixin(TransactionEditPermissionMixin, generic.edit.UpdateView):
    model = Transaction
    form_class = TransactionEditForm
    template_name = "transactions/edit.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_form(self):
        # get_success_url is run after object update so we need to save the data
        # we will need later
        self.old_person = self.object.person
        return super().get_form()


class TransactionEditFromPersonView(TransactionEditMixin):
    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.old_person.pk})


class TransactionEditView(TransactionEditMixin):
    success_url = reverse_lazy("transactions:index")


class TransactionDeleteView(TransactionEditPermissionMixin, generic.edit.DeleteView):
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
        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})


class TransactionIndexView(generic.list.ListView):
    model = Transaction
    template_name = "transactions/index.html"
    context_object_name = "transactions"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("filter_form", self.filter_form)

        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.filter_form = TransactionFilterForm(self.request.GET)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        transactions = Transaction.objects.all()

        if self.filter_form.is_valid():
            transactions = parse_transactions_filter_queryset(
                self.filter_form.cleaned_data, transactions
            )

        return transactions.order_by("date_due")


class MyTransactionsView(TransactionListMixin):
    template_name = "transactions/my_transactions.html"

    def get_object(self, queryset=None):
        return self.request.active_person
