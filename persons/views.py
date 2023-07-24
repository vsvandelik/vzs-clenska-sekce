from functools import reduce

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from features.models import FeatureTypeTexts
from groups.models import StaticGroup
from .forms import (
    PersonForm,
    AddManagedPersonForm,
    DeleteManagedPersonForm,
    PersonsFilterForm,
    MyProfileUpdateForm,
)
from .models import Person
from .utils import (
    parse_persons_filter_queryset,
    send_email_to_selected_persons,
    extend_kwargs_of_assignment_features,
)

from vzs.utils import export_queryset_csv


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
    template_name = "persons/index.html"
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
    template_name = "persons/detail.html"

    def get_context_data(self, **kwargs):
        extend_kwargs_of_assignment_features(self.kwargs["pk"], kwargs)

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
    template_name = "persons/edit.html"
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
    template_name = "persons/edit.html"
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
    template_name = "persons/delete.html"
    success_url = reverse_lazy("persons:index")
    success_message = _("Osoba byla úspěšně smazána")

    def get_queryset(self):
        return self._filter_queryset_by_permission()


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
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
        )

        return send_email_to_selected_persons(selected_persons)


class ExportSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        selected_persons = parse_persons_filter_queryset(
            self.request.GET,
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, Person.objects.with_age()
            ),
        )

        return export_queryset_csv("vzs_osoby_export", selected_persons)


class MyProfileView(generic.DetailView):
    model = Person
    template_name = "persons/my_profile.html"

    def get_object(self, queryset=None):
        return self.request.active_person

    def get_context_data(self, **kwargs):
        kwargs.setdefault("features_texts", FeatureTypeTexts)
        extend_kwargs_of_assignment_features(self.request.active_person, kwargs)

        return super().get_context_data(**kwargs)


class MyProfileUpdateView(SuccessMessageMixin, generic.edit.UpdateView):
    model = Person
    template_name = "persons/my_profile_edit.html"
    form_class = MyProfileUpdateForm
    success_message = _("Váš profil byl úspěšně upraven.")
    success_url = reverse_lazy("my-profile:index")

    def get_object(self, queryset=None):
        return self.request.active_person

    def form_invalid(self, form):
        messages.error(
            self.request, _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
        )
        return super().form_invalid(form)
