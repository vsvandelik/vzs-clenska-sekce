import csv
from functools import reduce

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

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


class PersonPermissionMixin(PermissionRequiredMixin):
    def has_permission(self):
        permission_required = (
            "persons.clenska_zakladna",
            "persons.detska_clenska_zakladna",
            "persons.bazenova_clenska_zakladna",
            "persons.lezecka_clenska_zakladna",
            "persons.dospela_clenska_zakladna",
        )
        for permission in permission_required:
            if self.request.user.has_perm(permission):
                return True

        return False

    @staticmethod
    def get_queryset_by_permission(user):
        if user.has_perm("persons.clenska_zakladna"):
            return Person.objects

        conditions = []

        if user.has_perm("persons.detska_clenska_zakladna"):
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("persons.bazenova_clenska_zakladna"):
            # TODO: omezit jen na bazenove treninky
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("persons.lezecka_clenska_zakladna"):
            # TODO: omezit jen na lezecke treninky
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("persons.dospela_clenska_zakladna"):
            conditions.append(
                Q(
                    person_type__in=[
                        Person.Type.ADULT,
                        Person.Type.EXTERNAL,
                        Person.Type.EXPECTANT,
                        Person.Type.HONORARY,
                    ]
                )
            )

        if not conditions:
            return Person.objects.none()

        return Person.objects.filter(reduce(lambda x, y: x | y, conditions))

    def _filter_queryset_by_permission(self):
        return self.get_queryset_by_permission(self.request.user)

    def _get_available_person_types(self):
        available_person_types = set()

        if self.request.user.has_perm("persons.clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.CHILD,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                    Person.Type.PARENT,
                ]
            )

        if (
            self.request.user.has_perm("persons.detska_clenska_zakladna")
            or self.request.user.has_perm("persons.bazenova_clenska_zakladna")
            or self.request.user.has_perm("persons.lezecka_clenska_zakladna")
        ):
            available_person_types.update([Person.Type.CHILD, Person.Type.PARENT])

        if self.request.user.has_perm("persons.dospela_clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                ]
            )

        return list(available_person_types)


class PersonIndexView(PersonPermissionMixin, generic.ListView):
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
        persons_objects = self._filter_queryset_by_permission()

        self.filter_form = PersonsFilterForm(self.request.GET)

        if self.filter_form.is_valid():
            return parse_persons_filter_queryset(self.request.GET, persons_objects)
        else:
            return persons_objects


class PersonDetailView(PersonPermissionMixin, generic.DetailView):
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
        context["persons_to_manage"] = (
            self._filter_queryset_by_permission()
            .exclude(managed_by=self.kwargs["pk"])
            .exclude(pk=self.kwargs["pk"])
        )
        return context

    def get_queryset(self):
        return self._filter_queryset_by_permission()


class PersonCreateView(
    PersonPermissionMixin, SuccessMessageMixin, generic.edit.CreateView
):
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["available_person_types"] = self._get_available_person_types()
        return kwargs


class PersonUpdateView(
    PersonPermissionMixin, SuccessMessageMixin, generic.edit.UpdateView
):
    model = Person
    template_name = "persons/persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně upravena")

    def form_invalid(self, form):
        messages.error(
            self.request, _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
        )
        return super().form_invalid(form)

    def get_queryset(self):
        return self._filter_queryset_by_permission()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["available_person_types"] = self._get_available_person_types()
        return kwargs


class PersonDeleteView(PersonPermissionMixin, generic.edit.DeleteView):
    model = Person
    template_name = "persons/persons/confirm_delete.html"
    success_url = reverse_lazy("persons:index")
    success_message = _("Osoba byla úspěšně smazána")

    def get_queryset(self):
        return self._filter_queryset_by_permission()


class FeaturePermissionMixin(PermissionRequiredMixin):
    def __init__(self):
        super().__init__()
        self.feature_type = None
        self.feature_type_texts = None
        self.person = None

    def dispatch(self, request, feature_type, *args, **kwargs):
        self.feature_type = feature_type
        self.feature_type_texts = FeatureTypeTexts[feature_type]
        if "person" in kwargs:
            self.person = kwargs["person"]
        return super().dispatch(request, feature_type, *args, **kwargs)

    def has_permission(self):
        user = self.request.user
        return user.has_perm(self.feature_type_texts.permission_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = self.feature_type_texts

        return context

    def get_person_with_permission_check(self):
        try:
            return PersonPermissionMixin.get_queryset_by_permission(
                self.request.user
            ).get(id=self.person)
        except Person.DoesNotExist:
            raise Http404()


class FeatureAssignEditView(FeaturePermissionMixin, generic.edit.UpdateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment/edit.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.person])

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["person"] = self.get_person_with_permission_check()
        context["features"] = Feature.objects.filter(
            feature_type=self.feature_type_texts.shortcut, assignable=True
        )

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form_labels = self.feature_type_texts.form_labels
        if form_labels:
            for field, label in form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def form_valid(self, form):
        form.instance.person = self.get_person_with_permission_check()

        if not form.instance.pk:
            success_message = self.feature_type_texts.success_message_assigned
        else:
            success_message = self.feature_type_texts.success_message_assigning_updated

        try:
            response = super().form_valid(form)
            messages.success(self.request, success_message)
            return response

        except IntegrityError:
            messages.error(
                self.request, self.feature_type_texts.duplicated_message_assigning
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        feature_name_4 = self.feature_type_texts.name_4
        messages.error(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
        return kwargs


class FeatureAssignDeleteView(
    FeaturePermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = FeatureAssignment
    template_name = "persons/features_assignment/delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.person])

    def get_success_message(self, cleaned_data):
        return self.feature_type_texts.success_message_assigning_delete

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.get_person_with_permission_check()
        return context


class FeatureIndexView(FeaturePermissionMixin, generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"persons/features/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_type"] = self.feature_type
        return context

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return (
            super()
            .get_queryset()
            .filter(feature_type=feature_type_params.shortcut, parent=None)
        )


class FeatureDetailView(FeaturePermissionMixin, generic.DetailView):
    model = Feature

    def get_template_names(self):
        return f"persons/features/detail.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_type"] = self.feature_type
        return context

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureEditView(FeaturePermissionMixin, generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm

    def get_template_names(self):
        return f"persons/features/edit.html"

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"{self.feature_type}:detail", args=(self.object.pk,))

    def form_valid(self, form):
        feature_type_texts = self.feature_type_texts
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
        feature_type_texts = self.feature_type_texts
        form = super().get_form(form_class)
        if feature_type_texts.form_labels:
            for field, label in feature_type_texts.form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
        return kwargs


class FeatureDeleteView(
    FeaturePermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = Feature

    def get_template_names(self):
        return f"persons/features/delete.html"

    def get_success_url(self):
        return reverse(f"{self.feature_type}:index")

    def get_success_message(self, cleaned_data):
        return self.feature_type_texts.success_message_delete


class GroupPermissionMixin(PermissionRequiredMixin):
    permission_required = "persons.spravce_skupin"


class GroupIndexView(GroupPermissionMixin, generic.ListView):
    model = Group
    template_name = "persons/groups/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["static_groups"] = StaticGroup.objects.all()
        context["dynamic_groups"] = StaticGroup.objects.all()
        return context


class GroupDeleteView(
    GroupPermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = StaticGroup
    template_name = "persons/groups/delete.html"
    success_url = reverse_lazy("persons:groups:index")
    success_message = "Skupina byla úspěšně smazána."


class StaticGroupDetailView(
    GroupPermissionMixin,
    SuccessMessageMixin,
    generic.DetailView,
    generic.edit.UpdateView,
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


class StaticGroupEditView(
    GroupPermissionMixin, SuccessMessageMixin, generic.edit.UpdateView
):
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


class StaticGroupRemoveMemberView(GroupPermissionMixin, generic.View):
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


class SyncGroupMembersWithGoogleView(GroupPermissionMixin, generic.View):
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


class AddDeleteManagedPersonMixin(PersonPermissionMixin, generic.View):
    http_method_names = ["post"]

    def process_form(self, request, form, pk, op, success_message, error_message):
        if form.is_valid():
            managing_person = form.cleaned_data["managing_person_instance"]
            new_managed_person = form.cleaned_data["managed_person_instance"]

            try:
                self._filter_queryset_by_permission().get(pk=new_managed_person.pk)
            except Person.DoesNotExist:
                raise Http404()

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
        selected_persons = parse_persons_filter_queryset(
            self.request.GET,
            PersonPermissionMixin.get_queryset_by_permission(self.request.user),
        )

        recipients = [
            f"{p.first_name} {p.last_name} <{p.email}>" for p in selected_persons
        ]

        gmail_link = "https://mail.google.com/mail/?view=cm&to=" + ",".join(recipients)

        return redirect(gmail_link)


class ExportSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        selected_persons = parse_persons_filter_queryset(
            self.request.GET,
            PersonPermissionMixin.get_queryset_by_permission(self.request.user),
        )

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


def parse_persons_filter_queryset(params_dict, persons):
    name = params_dict.get("name")
    email = params_dict.get("email")
    qualification = params_dict.get("qualifications")
    permission = params_dict.get("permissions")
    equipment = params_dict.get("equipments")
    person_type = params_dict.get("person_type")
    birth_year_from = params_dict.get("birth_year_from")
    birth_year_to = params_dict.get("birth_year_to")

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

    if birth_year_from:
        persons = persons.filter(date_of_birth__year__gte=birth_year_from)

    if birth_year_to:
        persons = persons.filter(date_of_birth__year__lte=birth_year_to)

    return persons.order_by("last_name")


class TransactionEditPermissionMixin(PermissionRequiredMixin):
    permission_required = "persons.spravce_transakci"


class TransactionCreateView(TransactionEditPermissionMixin, generic.edit.CreateView):
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

    def get_queryset(self):
        if self.request.user.has_perm("persons.spravce_transakci"):
            return super().get_queryset()
        else:
            return PersonPermissionMixin.get_queryset_by_permission(self.request.user)


class TransactionQRView(generic.detail.DetailView):
    template_name = "persons/transactions/QR.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        transaction = self.object

        if "person" not in context:
            context["person"] = transaction.person

        return context

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            Q(fio_transaction__isnull=True) & Q(amount__lt=0)
        )
        if not self.request.user.has_perm("persons.spravce_transakci"):
            queryset = queryset.filter(
                person__in=PersonPermissionMixin.get_queryset_by_permission(
                    self.request.user
                )
            )

        return queryset


class TransactionEditView(TransactionEditPermissionMixin, generic.edit.UpdateView):
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


class TransactionDeleteView(TransactionEditPermissionMixin, generic.edit.DeleteView):
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
