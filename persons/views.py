import csv
from functools import reduce

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.db.models import Q, Exists, OuterRef
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
    AddPersonToGroupForm,
    RemovePersonFromGroupForm,
)
from .models import (
    Person,
    FeatureAssignment,
    Feature,
    FeatureTypeTexts,
    Group,
    StaticGroup,
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
    def get_queryset_by_permission(user, queryset=None):
        if queryset is None:
            queryset = Person.objects

        if user.has_perm("persons.clenska_zakladna"):
            return queryset

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
            return queryset.none()

        return queryset.filter(reduce(lambda x, y: x | y, conditions))

    def _filter_queryset_by_permission(self, queryset=None):
        return self.get_queryset_by_permission(self.request.user, queryset)

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_form = None

    def get_context_data(self, **kwargs):
        kwargs.setdefault("filter_form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        persons_objects = self._filter_queryset_by_permission(Person.objects.with_age())

        self.filter_form = PersonsFilterForm(self.request.GET)

        if self.filter_form.is_valid():
            return parse_persons_filter_queryset(self.request.GET, persons_objects)
        else:
            return persons_objects


class PersonDetailView(PersonPermissionMixin, generic.DetailView):
    model = Person
    template_name = "persons/persons/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "qualifications",
            FeatureAssignment.objects.filter(
                person=self.kwargs["pk"],
                feature__feature_type=Feature.Type.QUALIFICATION.value,
            ),
        )

        kwargs.setdefault(
            "permissions",
            FeatureAssignment.objects.filter(
                person=self.kwargs["pk"],
                feature__feature_type=Feature.Type.PERMISSION.value,
            ),
        )

        kwargs.setdefault(
            "equipments",
            FeatureAssignment.objects.filter(
                person=self.kwargs["pk"],
                feature__feature_type=Feature.Type.EQUIPMENT.value,
            ),
        )

        kwargs.setdefault(
            "persons_to_manage",
            self._filter_queryset_by_permission()
            .exclude(managed_by=self.kwargs["pk"])
            .exclude(pk=self.kwargs["pk"])
            .order_by("last_name", "first_name"),
        )

        user_groups = Person.objects.get(pk=self.kwargs["pk"]).groups.all()
        kwargs.setdefault(
            "available_groups", StaticGroup.objects.exclude(pk__in=user_groups)
        )

        kwargs.setdefault("features_texts", FeatureTypeTexts)

        return super().get_context_data(**kwargs)

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
    template_name = "persons/persons/delete.html"
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
        kwargs.setdefault("texts", self.feature_type_texts)
        kwargs.setdefault("feature_type", self.feature_type)

        return super().get_context_data(**kwargs)

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
        kwargs.setdefault("person", self.get_person_with_permission_check())
        kwargs.setdefault(
            "features",
            Feature.objects.filter(
                feature_type=self.feature_type_texts.shortcut, assignable=True
            ),
        )

        return super().get_context_data(**kwargs)

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
            form.add_transaction_if_necessary()
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
        kwargs.setdefault("person", self.get_person_with_permission_check())

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        if (
            hasattr(self.object, "transaction")
            and not self.object.transaction.is_settled()
        ):
            self.object.transaction.delete()

        return super().form_valid(form)


class FeatureIndexView(FeaturePermissionMixin, generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"persons/features/index.html"

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureDetailView(FeaturePermissionMixin, generic.DetailView):
    model = Feature

    def get_context_data(self, **kwargs):
        kwargs.setdefault("assignment_matrix", self._get_features_assignment_matrix())

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        return f"persons/features/detail.html"

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)

    def _get_features_assignment_matrix(self):
        all_features = (
            self.object.get_descendants(include_self=True)
            .filter(assignable=True)
            .prefetch_related("featureassignment_set")
        )

        all_persons = Person.objects.filter(
            featureassignment__feature__in=all_features
        ).distinct()

        features_assignment_matrix = {
            "columns": all_features,
            "rows": [],
        }

        for person in all_persons:
            features = all_features.annotate(
                is_assigned=Exists(
                    FeatureAssignment.objects.filter(
                        person=person, feature=OuterRef("pk")
                    )
                )
            ).values_list("is_assigned", flat=True)

            features_assignment_matrix["rows"].append(
                {
                    "person": person,
                    "features": list(features),
                }
            )

        return features_assignment_matrix


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

    def get_context_data(self, **kwargs):
        kwargs.setdefault("static_groups", StaticGroup.objects.all())
        kwargs.setdefault("dynamic_groups", [])

        return super().get_context_data(**kwargs)


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
        kwargs.setdefault(
            "available_persons",
            Person.objects.exclude(
                Q(groups__isnull=False) & Q(groups__id=self.object.pk)
            ),
        )

        return super().get_context_data(**kwargs)

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


class AddRemovePersonToGroupMixin(PersonPermissionMixin, generic.View):
    http_method_names = ["post"]

    ADD_TO_GROUP = "add"
    REMOVE_FROM_GROUP = "remove"

    def process_form(
        self, request, form, person_pk, op, success_message, error_message
    ):
        if form.is_valid():
            group = form.cleaned_data["group"]

            if op == self.ADD_TO_GROUP:
                group.members.add(person_pk)
            else:
                group.members.remove(person_pk)

            messages.success(request, success_message)

        else:
            person_error_messages = " ".join(form.errors["group"])
            messages.error(request, error_message + person_error_messages)

        return redirect(reverse("persons:detail", args=[person_pk]))


class AddPersonToGroupView(AddRemovePersonToGroupMixin):
    def post(self, request, pk):
        form = AddPersonToGroupForm(request.POST, person=Person.objects.get(pk=pk))

        return self.process_form(
            request,
            form,
            pk,
            AddRemovePersonToGroupMixin.ADD_TO_GROUP,
            _("Osoba byla úspěšně přidána do skupiny."),
            _("Nepodařilo se přidat osobu do skupiny. "),
        )


class RemovePersonFromGroupView(AddRemovePersonToGroupMixin):
    def post(self, request, pk):
        form = RemovePersonFromGroupForm(request.POST, person=Person.objects.get(pk=pk))

        return self.process_form(
            request,
            form,
            pk,
            AddRemovePersonToGroupMixin.REMOVE_FROM_GROUP,
            _("Osoba byla úspěšně odebrána ze skupiny."),
            _("Nepodařilo se odebrat osobu ze skupiny. "),
        )


class SendEmailToSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        selected_persons = parse_persons_filter_queryset(
            self.request.GET,
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
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
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
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
