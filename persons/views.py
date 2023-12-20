from functools import reduce

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from features.models import FeatureTypeTexts
from groups.models import Group
from vzs.mixin_extensions import MessagesMixin
from vzs.utils import export_queryset_csv, filter_queryset

from .forms import (
    AddManagedPersonForm,
    DeleteManagedPersonForm,
    MyProfileUpdateForm,
    PersonForm,
    PersonHourlyRateForm,
    PersonsFilterForm,
)
from .models import Person, get_active_user
from .utils import (
    PersonsFilter,
    extend_kwargs_of_assignment_features,
    send_email_to_selected_persons,
)


class PersonPermissionBaseMixin:
    @staticmethod
    def permission_predicate(request):
        permission_required = (
            "persons.clenska_zakladna",
            "persons.detska_clenska_zakladna",
            "persons.bazenova_clenska_zakladna",
            "persons.lezecka_clenska_zakladna",
            "persons.dospela_clenska_zakladna",
        )
        for permission in permission_required:
            if get_active_user(request.active_person).has_perm(permission):
                return True

        return False


class PersonPermissionMixin(PersonPermissionBaseMixin, PermissionRequiredMixin):
    def has_permission(self):
        return self.permission_predicate(self.request)

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
                        Person.Type.FORMER,
                    ]
                )
            )

        if not conditions:
            return queryset.none()

        return queryset.filter(reduce(lambda x, y: x | y, conditions))

    def _filter_queryset_by_permission(self, queryset=None):
        return self.get_queryset_by_permission(
            get_active_user(self.request.active_person), queryset
        )

    def _get_available_person_types(self):
        available_person_types = set()

        active_user = get_active_user(self.request.active_person)

        if active_user.has_perm("persons.clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.CHILD,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                    Person.Type.PARENT,
                    Person.Type.FORMER,
                ]
            )

        if (
            active_user.has_perm("persons.detska_clenska_zakladna")
            or active_user.has_perm("persons.bazenova_clenska_zakladna")
            or active_user.has_perm("persons.lezecka_clenska_zakladna")
        ):
            available_person_types.update([Person.Type.CHILD, Person.Type.PARENT])

        if active_user.has_perm("persons.dospela_clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                    Person.Type.FORMER,
                ]
            )

        return list(available_person_types)


class PersonPermissionQuerysetMixin:
    def get_queryset(self):
        return self._filter_queryset_by_permission()


class PersonIndexView(PersonPermissionMixin, ListView):
    context_object_name = "persons"
    model = Person
    template_name = "persons/index.html"

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

        filter_dict = self.request.GET if self.filter_form.is_valid() else None

        return filter_queryset(persons_objects, filter_dict, PersonsFilter).order_by(
            "last_name"
        )


class PersonDetailView(
    PersonPermissionQuerysetMixin, PersonPermissionMixin, DetailView
):
    model = Person
    template_name = "persons/detail.html"

    def get_context_data(self, **kwargs):
        person: Person = self.object

        extend_kwargs_of_assignment_features(person, kwargs)

        kwargs.setdefault(
            "persons_to_manage",
            self._filter_queryset_by_permission()
            .exclude(managed_by=person)
            .exclude(pk=person.pk)
            .order_by("last_name", "first_name"),
        )

        kwargs.setdefault(
            "available_groups", Group.objects.exclude(pk__in=person.groups.all())
        )

        kwargs.setdefault("features_texts", FeatureTypeTexts)

        return super().get_context_data(**kwargs)


class PersonCreateUpdateMixin(PersonPermissionMixin, MessagesMixin):
    form_class = PersonForm
    model = Person
    template_name = "persons/edit.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs["available_person_types"] = self._get_available_person_types()

        return kwargs


class PersonCreateView(PersonCreateUpdateMixin, CreateView):
    error_message = _("Nepodařilo se vytvořit novou osobu. Opravte chyby ve formuláři.")
    success_message = _("Osoba byla úspěšně vytvořena")


class PersonUpdateView(
    PersonPermissionQuerysetMixin, PersonCreateUpdateMixin, UpdateView
):
    error_message = _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
    success_message = _("Osoba byla úspěšně upravena")


class PersonDeleteView(
    PersonPermissionQuerysetMixin, PersonPermissionMixin, DeleteView
):
    model = Person
    success_message = _("Osoba byla úspěšně smazána")
    success_url = reverse_lazy("persons:index")
    template_name = "persons/delete.html"


class AddDeleteManagedPersonMixin(PersonPermissionMixin, MessagesMixin, UpdateView):
    error_message: str
    http_method_names = ["post"]
    model = Person

    def get_error_message(self, errors):
        return self.error_message + " ".join(errors["managed_person"])


class AddManagedPersonView(AddDeleteManagedPersonMixin):
    error_message = _("Nepodařilo se uložit novou spravovanou osobu. ")
    form_class = AddManagedPersonForm
    success_message = _("Nová spravovaná osoba byla přidána.")


class DeleteManagedPersonView(AddDeleteManagedPersonMixin):
    error_message = _("Nepodařilo se odebrat spravovanou osobu. ")
    form_class = DeleteManagedPersonForm
    success_message = _("Odebrání spravované osoby bylo úspěšné.")


class EditHourlyRateView(PersonPermissionMixin, SuccessMessageMixin, UpdateView):
    form_class = PersonHourlyRateForm
    model = Person
    success_message = _("Hodinové sazby byly úspěšně upraveny.")
    template_name = "persons/edit_hourly_rate.html"


class SelectedPersonsMixin(View):
    http_method_names = ["get"]

    def _get_queryset(self):
        raise NotImplementedError

    def _process_selected_persons(self, selected_persons):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        selected_persons = filter_queryset(
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, self._get_queryset()
            ),
            request.GET,
            PersonsFilter,
        )

        return self._process_selected_persons(selected_persons)


class SendEmailToSelectedPersonsView(SelectedPersonsMixin):
    def _get_queryset(self):
        return Person.objects.all()

    def _process_selected_persons(self, selected_persons):
        return send_email_to_selected_persons(selected_persons)


class ExportSelectedPersonsView(SelectedPersonsMixin):
    def _get_queryset(self):
        return Person.objects.with_age()

    def _process_selected_persons(self, selected_persons):
        return export_queryset_csv("vzs_osoby_export", selected_persons)


class MyProfileView(LoginRequiredMixin, DetailView):
    model = Person
    template_name = "persons/my_profile.html"

    def get_object(self, queryset=None):
        return self.request.active_person

    def get_context_data(self, **kwargs):
        kwargs.setdefault("features_texts", FeatureTypeTexts)
        extend_kwargs_of_assignment_features(self.request.active_person, kwargs)

        return super().get_context_data(**kwargs)


class MyProfileUpdateView(LoginRequiredMixin, MessagesMixin, UpdateView):
    error_message = _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
    form_class = MyProfileUpdateForm
    model = Person
    success_message = _("Váš profil byl úspěšně upraven.")
    success_url = reverse_lazy("my-profile:index")
    template_name = "persons/my_profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.active_person
