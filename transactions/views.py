from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from persons.models import Person
from persons.views import PersonPermissionMixin
from .forms import TransactionEditForm, TransactionCreateForm
from .models import Transaction


class TransactionEditPermissionMixin(PermissionRequiredMixin):
    permission_required = "transactions.spravce_transakci"


class TransactionCreateView(TransactionEditPermissionMixin, generic.edit.CreateView):
    model = Transaction
    form_class = TransactionCreateForm
    template_name = "transactions/create.html"

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


class TransactionListView(generic.detail.DetailView):
    model = Person
    template_name = "transactions/list.html"

    def _get_transactions(self, person):
        raise ImproperlyConfigured("_get_transactions needs to be overridden.")

    def get_context_data(self, **kwargs):
        person = self.object
        transactions = person.transactions

        Q_debt = Q(amount__lt=0)
        Q_award = Q(amount__gt=0)

        transactions_debt = transactions.filter(Q_debt)
        transactions_reward = transactions.filter(Q_award)

        transactions_due = transactions.filter(fio_transaction__isnull=True)
        transactions_current_debt = transactions_due.filter(Q_debt)
        transactions_due_reward = transactions_due.filter(Q_award)

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


class TransactionEditView(TransactionEditPermissionMixin, generic.edit.UpdateView):
    model = Transaction
    form_class = TransactionEditForm
    template_name = "transactions/edit.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.object.person.pk})


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