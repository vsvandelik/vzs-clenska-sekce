import csv
import datetime

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.core.exceptions import ImproperlyConfigured

from google_integration import google_directory
from .forms import (
    PersonForm,
    FeatureAssignmentForm,
    FeatureForm,
    StaticGroupForm,
    AddMembersStaticGroupForm,
    AddManagedPersonForm,
    DeleteManagedPersonForm,
    PersonsFilterForm,
    TransactionCreateForm,
    TransactionEditForm,
)
from .models import (
    Person,
    FeatureAssignment,
    Feature,
    FeatureTypeTexts,
    Group,
    StaticGroup,
    Transaction,
)
from .utils import sync_single_group_with_google
from vzs import settings


class PersonIndexView(generic.ListView):
    model = Person
    template_name = "persons/persons/index.html"
    context_object_name = "persons"
    paginate_by = 20

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_form = None

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["filtered_get"] = self.request.GET.urlencode()
        return context

    def get_queryset(self):
        self.filter_form = PersonsFilterForm(self.request.GET)

        if self.filter_form.is_valid():
            return parse_persons_filter_queryset(self.request.GET)
        else:
            return Person.objects.all()


class PersonDetailView(generic.DetailView):
    model = Person
    template_name = "persons/persons/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qualifications"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.QUALIFICATION.value,
        )
        context["permissions"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.PERMISSION.value,
        )
        context["equipments"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.EQUIPMENT.value,
        )
        context["persons_to_manage"] = Person.objects.exclude(
            managed_by=self.kwargs["pk"]
        ).exclude(pk=self.kwargs["pk"])
        return context


class PersonCreateView(SuccessMessageMixin, generic.edit.CreateView):
    model = Person
    template_name = "persons/persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně vytvořena")

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Nepodařilo se vytvořit novou osobu. Opravte chyby ve formuláři."),
        )
        return super().form_invalid(form)


class PersonUpdateView(SuccessMessageMixin, generic.edit.UpdateView):
    model = Person
    template_name = "persons/persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně upravena")

    def form_invalid(self, form):
        messages.error(
            self.request, _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
        )
        return super().form_invalid(form)


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = "persons/persons/delete.html"
    success_url = reverse_lazy("persons:index")
    success_message = _("Osoba byla úspěšně smazána")


class FeatureAssignEditView(generic.edit.UpdateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment/edit.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["texts"] = feature_type_texts
        context["features"] = Feature.objects.filter(
            feature_type=feature_type_texts.shortcut, assignable=True
        )
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form_labels = FeatureTypeTexts[self.kwargs["feature_type"]].form_labels
        if form_labels:
            for field, label in form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def form_valid(self, form):
        form.instance.person = get_object_or_404(Person, id=self.kwargs["person"])
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]

        if not form.instance.pk:
            success_message = feature_type_texts.success_message_assigned
        else:
            success_message = feature_type_texts.success_message_assigning_updated

        try:
            response = super().form_valid(form)
            messages.success(self.request, success_message)
            return response

        except IntegrityError:
            messages.error(
                self.request, feature_type_texts.duplicated_message_assigning
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        feature_name_4 = FeatureTypeTexts[self.kwargs["feature_type"]].name_4
        messages.error(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = FeatureTypeTexts[self.kwargs["feature_type"]].shortcut
        return kwargs


class FeatureAssignDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = FeatureAssignment
    template_name = "persons/features_assignment/delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[
            self.kwargs["feature_type"]
        ].success_message_assigning_delete

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        feature_type = self.kwargs["feature_type"]

        context["feature_type"] = feature_type
        context["texts"] = FeatureTypeTexts[feature_type]
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context


class FeatureIndexView(generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"persons/features/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["feature_type"] = self.kwargs["feature_type"]
        return context

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return (
            super()
            .get_queryset()
            .filter(feature_type=feature_type_params.shortcut, parent=None)
        )


class FeatureDetailView(generic.DetailView):
    model = Feature

    def get_template_names(self):
        return f"persons/features/detail.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["feature_type"] = self.kwargs["feature_type"]
        return context

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureEditView(generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm

    def get_template_names(self):
        return f"persons/features/edit.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        return context

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:detail", args=(self.object.pk,))

    def form_valid(self, form):
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        form.instance.feature_type = feature_type_texts.shortcut
        messages.success(self.request, feature_type_texts.success_message_save)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Formulář se nepodařilo uložit. Opravte chyby a zkuste to znovu."),
        )
        return super().form_invalid(form)

    def get_form(self, form_class=None):
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        form = super().get_form(form_class)
        if feature_type_texts.form_labels:
            for field, label in feature_type_texts.form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = FeatureTypeTexts[self.kwargs["feature_type"]].shortcut
        return kwargs


class FeatureDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = Feature

    def get_template_names(self):
        return f"persons/features/delete.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        return context

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:index")

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[self.kwargs["feature_type"]].success_message_delete


class GroupIndexView(generic.ListView):
    model = Group
    template_name = "persons/groups/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["static_groups"] = StaticGroup.objects.all()
        context["dynamic_groups"] = StaticGroup.objects.all()
        return context


class GroupDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = StaticGroup
    template_name = "persons/groups/delete.html"
    success_url = reverse_lazy("persons:groups:index")
    success_message = "Skupina byla úspěšně smazána."


class StaticGroupDetailView(
    SuccessMessageMixin, generic.DetailView, generic.edit.UpdateView
):
    model = StaticGroup
    form_class = AddMembersStaticGroupForm
    success_message = "Osoby byly úspěšně přidány."
    template_name = "persons/groups/detail_static.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_persons"] = Person.objects.exclude(
            Q(groups__isnull=False) & Q(groups__id=self.object.pk)
        )
        return context

    def get_success_url(self):
        return reverse("persons:groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        new_members = form.cleaned_data["members"]

        existing_members = self.object.members.all()
        combined_members = existing_members | new_members

        form.instance.members.set(combined_members)

        if form.instance.google_email:
            for new_member in new_members:
                google_directory.add_member_to_group(
                    new_member.email, form.instance.google_email
                )

        messages.success(self.request, self.success_message)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Nepodařilo se přidat osoby."))
        return super().form_invalid(form)


class StaticGroupEditView(SuccessMessageMixin, generic.edit.UpdateView):
    model = StaticGroup
    form_class = StaticGroupForm
    template_name = "persons/groups/edit_static.html"
    success_message = "Statická skupina byla úspěšně uložena."

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"persons:groups:detail", args=(self.object.pk,))

    def form_invalid(self, form):
        messages.error(self.request, _("Skupinu se nepodařilo uložit."))
        return super().form_invalid(form)


class StaticGroupRemoveMemberView(generic.View):
    success_message = "Osoba byla odebrána."

    def get_success_url(self):
        return reverse("persons:groups:detail", args=(self.kwargs["group"],))

    def get(self, request, *args, **kwargs):
        member_to_remove = self.kwargs["person"]

        static_group = get_object_or_404(StaticGroup, id=self.kwargs["group"])
        static_group.members.remove(member_to_remove)

        if static_group.google_email:
            google_directory.remove_member_from_group(
                Person.objects.get(pk=member_to_remove).email, static_group.google_email
            )

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class SyncGroupMembersWithGoogleView(generic.View):
    http_method_names = ["get"]

    def get(self, request, group=None):
        if group:
            group_instance = get_object_or_404(StaticGroup, pk=group)
            if not group_instance.google_email:
                messages.error(
                    request,
                    _(
                        "Zvolená skupina nemá zadanou google e-mailovou adresu, a proto nemůže být sychronizována."
                    ),
                )
                return redirect(
                    reverse("persons:groups:detail", args=[group_instance.pk])
                )

            sync_single_group_with_google(group_instance)
            messages.success(
                request,
                _("Synchronizace skupiny %s s Google Workplace byla úspěšná.")
                % group_instance.name,
            )
            return redirect(reverse("persons:groups:detail", args=[group_instance.pk]))

        else:
            for group in StaticGroup.objects.filter(google_email__isnull=False):
                sync_single_group_with_google(group)

            messages.success(
                request,
                _("Synchronizace všech skupin s Google Workplace byla úspěšná."),
            )
            return redirect(reverse("persons:groups:index"))


class AddDeleteManagedPersonMixin(generic.View):
    http_method_names = ["post"]

    def process_form(self, request, form, pk, op, success_message, error_message):
        if form.is_valid():
            managing_person = form.cleaned_data["managing_person_instance"]
            new_managed_person = form.cleaned_data["managed_person_instance"]

            if op == "add":
                managing_person.managed_persons.add(new_managed_person)
            else:
                managing_person.managed_persons.remove(new_managed_person)

            messages.success(request, success_message)

        else:
            person_error_messages = " ".join(form.errors["person"])
            messages.error(request, error_message + person_error_messages)

        return redirect(reverse("persons:detail", args=[pk]))


class AddManagedPersonView(AddDeleteManagedPersonMixin):
    def post(self, request, pk):
        form = AddManagedPersonForm(request.POST, managing_person=pk)

        return self.process_form(
            request,
            form,
            pk,
            "add",
            _("Nová spravovaná osoba byla přidána."),
            _("Nepodařilo se uložit novou spravovanou osobu. "),
        )


class DeleteManagedPersonView(AddDeleteManagedPersonMixin):
    def post(self, request, pk):
        form = DeleteManagedPersonForm(request.POST, managing_person=pk)

        return self.process_form(
            request,
            form,
            pk,
            "delete",
            _("Odebrání spravované osoby bylo úspěšné."),
            _("Nepodařilo se odebrat spravovanou osobu. "),
        )


class SendEmailToSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        selected_persons = parse_persons_filter_queryset(self.request.GET)

        recipients = [
            f"{p.first_name} {p.last_name} <{p.email}>" for p in selected_persons
        ]

        gmail_link = "https://mail.google.com/mail/?view=cm&to=" + ",".join(recipients)

        return redirect(gmail_link)


class ExportSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        selected_persons = parse_persons_filter_queryset(self.request.GET)

        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="vzs_osoby_export.csv"'
            },
        )
        response.write("\ufeff".encode("utf8"))

        writer = csv.writer(response, delimiter=";")

        labels = []
        keys = []

        for field in Person._meta.get_fields():
            if field.is_relation:
                continue

            labels.append(
                field.verbose_name if hasattr(field, "verbose_name") else field.name
            )
            keys.append(field.name)

        writer.writerow(labels)  # header

        for person in selected_persons:
            writer.writerow([getattr(person, key) for key in keys])

        return response


def parse_persons_filter_queryset(params_dict):
    persons = Person.objects.with_age()

    name = params_dict.get("name")
    email = params_dict.get("email")
    qualification = params_dict.get("qualifications")
    permission = params_dict.get("permissions")
    equipment = params_dict.get("equipments")
    person_type = params_dict.get("person_type")
    age_from = params_dict.get("age_from")
    age_to = params_dict.get("age_to")

    if name:
        persons = persons.filter(
            Q(first_name__icontains=name) | Q(last_name__icontains=name)
        )

    if email:
        persons = persons.filter(email__icontains=email)

    if qualification:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.QUALIFICATION.value,
            featureassignment__feature__id=qualification,
        )

    if permission:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.PERMISSION.value,
            featureassignment__feature__id=permission,
        )

    if equipment:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.EQUIPMENT.value,
            featureassignment__feature__id=equipment,
        )

    if person_type:
        persons = persons.filter(person_type=person_type)

    if age_from:
        persons = persons.filter(age__gte=age_from)

    if age_to:
        persons = persons.filter(age__lte=age_to)

    return persons.order_by("last_name")


class TransactionCreateView(generic.edit.CreateView):
    model = Transaction
    form_class = TransactionCreateForm
    template_name = "persons/transactions/create.html"

    def dispatch(self, request, *args, **kwargs):
        self.person = get_object_or_404(Person, pk=self.kwargs["person"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "person" not in context:
            context["person"] = self.person

        return context

    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs["person"] = self.person

        return kwargs


class TransactionListView(generic.detail.DetailView):
    model = Person
    template_name = "persons/transactions/list.html"

    def _get_transactions(self, person):
        raise ImproperlyConfigured("_get_transactions needs to be overridden.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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

        if "transactions_debt" not in context:
            context["transactions_debt"] = transactions_debt

        if "transactions_reward" not in context:
            context["transactions_reward"] = transactions_reward

        if "current_debt" not in context:
            context["current_debt"] = current_debt

        if "due_reward" not in context:
            context["due_reward"] = due_reward

        return context


class TransactionQRView(generic.detail.DetailView):
    queryset = Transaction.objects.filter(
        Q(fio_transaction__isnull=True) & Q(amount__lt=0)
    )
    template_name = "persons/transactions/QR.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        transaction = self.object

        if "person" not in context:
            context["person"] = transaction.person

        return context


class TransactionEditView(generic.edit.UpdateView):
    model = Transaction
    form_class = TransactionEditForm
    template_name = "persons/transactions/edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        transaction = self.object

        if "person" not in context:
            context["person"] = transaction.person

        return context

    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.object.person.pk})


class TransactionDeleteView(generic.edit.DeleteView):
    model = Transaction
    template_name = "persons/transactions/delete.html"

    def form_valid(self, form):
        # success_message is sent after object deletion so we need to save the data
        # we will need later
        self.person = self.object.person
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "person" not in context:
            context["person"] = self.object.person

        return context

    def get_success_url(self):
        return reverse("persons:transaction-list", kwargs={"pk": self.person.pk})
