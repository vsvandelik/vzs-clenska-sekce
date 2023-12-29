import datetime
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from features.models import FeatureTypeTexts, Feature, FeatureAssignment
from groups.models import Group
from one_time_events.models import (
    OneTimeEvent,
    OneTimeEventAttendance,
    OneTimeEventOccurrence,
)
from persons.models import Person
from trainings.models import TrainingOccurrence
from vzs.mixin_extensions import MessagesMixin
from vzs.utils import export_queryset_csv, filter_queryset, today, now
from .forms import (
    AddManagedPersonForm,
    DeleteManagedPersonForm,
    MyProfileUpdateForm,
    PersonForm,
    PersonHourlyRateForm,
    PersonsFilterForm,
    PersonStatsForm,
)
from .permissions import PersonPermissionMixin, PersonPermissionQuerysetMixin
from .utils import (
    PersonsFilter,
    extend_kwargs_of_assignment_features,
    send_email_to_selected_persons,
    anonymize_person,
)


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


class PersonCreateChildView(PersonPermissionMixin, CreateView):
    form_class = PersonForm
    model = Person
    template_name = "persons/create_child.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["available_person_types"] = [Person.Type.CHILD]
        return kwargs


class PersonStatsView(PersonPermissionMixin, UpdateView):
    model = Person
    template_name = "persons/stats.html"
    form_class = PersonStatsForm
    http_method_names = ["get"]

    def _get_parse_dates(self):
        year = today().year
        default_dates = [
            date(year=year, month=1, day=1),
            date(year=year, month=12, day=31),
        ]
        start = self.request.GET.get("date_start", default_dates[0])
        end = self.request.GET.get("date_end", default_dates[1])
        dates = [start, end]
        invalid = 0
        for i in range(len(dates)):
            if type(dates[i]) is str:
                try:
                    d = datetime.strptime(dates[i], "%d. %m. %Y").date()
                    dates[i] = d
                except ValueError:
                    dates[i] = default_dates[i]
                    invalid += 1
        if dates[0] > dates[1] and (len(self.request.GET) == 1 or invalid == 1):
            if dates[0] != default_dates[0]:
                dates[1] = date(
                    year=dates[0].year, month=dates[1].month, day=dates[1].day
                )
            else:
                dates[0] = date(
                    year=dates[1].year, month=dates[0].month, day=dates[0].day
                )

        return dates[0], dates[1]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["date_start"] = self.date_start
        kwargs["date_end"] = self.date_end
        return kwargs

    def _get_stats(self):
        person = self.object
        one_time_event_categories = OneTimeEvent.Category.choices
        one_time_event_categories = sorted(
            one_time_event_categories, key=lambda x: x[1], reverse=False
        )
        one_time_events_query = """
                select SUM(one_time_event_occurrence.hours) from one_time_events_organizeroccurrenceassignment as organizer_assignment
                join persons_person as person on organizer_assignment.person_id = person.id
                join events_eventoccurrence as occurrence on organizer_assignment.occurrence_id = occurrence.id
                join one_time_events_onetimeeventoccurrence as one_time_event_occurrence on occurrence.id = one_time_event_occurrence.eventoccurrence_ptr_id
                join events_event as event on event.id = occurrence.event_id
                join one_time_events_onetimeevent as one_time_event on one_time_event.event_ptr_id = event.id
                where 
                organizer_assignment.state = %s
                and person.id = %s
                and one_time_event.category = %s
                and one_time_event_occurrence.date between %s and %s
        """
        one_time_events_out = []
        with connection.cursor() as cursor:
            for category in one_time_event_categories:
                value = category[0]
                label = category[1]
                cursor.execute(
                    one_time_events_query,
                    [
                        OneTimeEventAttendance.PRESENT.value,
                        person.id,
                        value,
                        str(self.date_start),
                        str(self.date_end),
                    ],
                )
                row = cursor.fetchone()
                sum = row[0] if row[0] is not None else 0
                one_time_events_out.append((label, sum))

            return one_time_events_out

    def get_context_data(self, **kwargs):
        self.date_start, self.date_end = self._get_parse_dates()
        kwargs.setdefault("stats", self._get_stats())
        return super().get_context_data(**kwargs)


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

    def form_valid(self, form):
        person = self.object

        if self._is_person_in_events(person, only_upcoming=True):
            messages.error(
                self.request,
                _(
                    "Osoba je přihlášena na nadcházející akce, a proto se osobu nepodařilo odstranit."
                ),
            )
            return HttpResponseRedirect(
                reverse("persons:detail", kwargs={"pk": person.pk})
            )

        if self._has_person_equipment(person):
            messages.error(
                self.request,
                _("Osoba má v držení vybavení, a proto se osobu nepodařilo odstranit."),
            )
            return HttpResponseRedirect(
                reverse("persons:detail", kwargs={"pk": person.pk})
            )

        if self._is_person_in_events(person):
            anonymize_person(person)
            messages.warning(
                self.request,
                _(
                    "Osoba je přihlášena na některé akce, proto nebude záznam o osobě smazán, ale bude jen anonymizován."
                ),
            )
        else:
            person.delete()
            messages.success(self.request, _("Osoba byla úspěšně smazána."))

        return HttpResponseRedirect(self.get_success_url())

    @staticmethod
    def _is_person_in_events(person, only_upcoming=False):
        one_time_occurrences = OneTimeEventOccurrence.objects.filter(
            Q(organizers=person) | Q(participants=person)
        )

        trainings_occurrences = TrainingOccurrence.objects.filter(
            Q(coaches=person) | Q(participants=person)
        )

        if only_upcoming:
            one_time_occurrences = one_time_occurrences.filter(date__gte=today())
            trainings_occurrences = trainings_occurrences.filter(
                datetime_start__gte=now()
            )

        return one_time_occurrences.exists() or trainings_occurrences.exists()

    @staticmethod
    def _has_person_equipment(person):
        equipment = (
            FeatureAssignment.objects.filter(
                person=person, feature__feature_type=Feature.Type.EQUIPMENT
            )
            .filter(Q(date_returned__isnull=True) | Q(date_returned__gte=today()))
            .all()
        )

        return equipment


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
