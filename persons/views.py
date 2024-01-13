from datetime import date, datetime

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from features.models import Feature, FeatureAssignment, FeatureTypeTexts
from groups.models import Group
from one_time_events.models import (
    OneTimeEvent,
    OneTimeEventAttendance,
    OneTimeEventOccurrence,
)
from persons.models import Person
from trainings.models import TrainingOccurrence
from users.permissions import LoginRequiredMixin
from vzs.mixins import MessagesMixin
from vzs.utils import export_queryset_csv, filter_queryset, now, today

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
    anonymize_person,
    extend_kwargs_of_assignment_features,
    send_email_to_selected_persons,
)


class PersonIndexView(PersonPermissionMixin, ListView):
    """
    Displays a list of all persons.

    Allow direct deletion using modals.

    Filters regular transactions using :class:`PersonsFilterForm`.

    **Permissions**:

    Users with ``*clenska_zakladna`` permissions see the corresponding set of persons.

    **Query parameters:**

    *   ``name``
    *   ``email``
    *   ``qualification``
    *   ``permission``
    *   ``equipment``
    *   ``person_type``
    *   ``age_from``
    *   ``age_to``
    """

    context_object_name = "persons"
    """:meta private:"""

    model = Person
    """:meta private:"""

    template_name = "persons/index.html"
    """:meta private:"""

    def __init__(self, **kwargs):
        """:meta private:"""

        super().__init__(**kwargs)
        self.filter_form = None

    def get_context_data(self, **kwargs):
        """
        *   ``filter_form`` - the :class:`PersonsFilterForm`
        *   ``filtered_get`` - url encoded GET parameters
            that were used to filter the persons
        """

        kwargs.setdefault("filter_form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """
        Orders the persons by their last name.
        """

        persons_objects = self._filter_queryset_by_permission(Person.objects.with_age())

        self.filter_form = PersonsFilterForm(self.request.GET)

        filter_dict = self.request.GET if self.filter_form.is_valid() else None

        return filter_queryset(persons_objects, filter_dict, PersonsFilter).order_by(
            "last_name"
        )


class PersonDetailView(
    PersonPermissionQuerysetMixin, PersonPermissionMixin, DetailView
):
    """
    Displays an admin view of a person.

    See :func:`get_queryset` for more information.

    **Permissions**:

    *   users that manage the person's membership type

    **Path parameters:**

    *   ``pk`` - ID of the person
    """

    model = Person
    """:meta private:"""

    template_name = "persons/detail.html"
    """:meta private:"""

    def get_context_data(self, **kwargs):
        """
        *   ``qualifications`` - qualifications of the person
        *   ``permissions`` - permissions of the person
        *   ``equipment`` - equipment of the person
        *   ``persons_to_manage`` - persons that could be managed by the person
            but are not
        *   ``available_groups`` - groups that the person could be a part of but is not
        *   ``features_texts`` - helper for Czech translations
            of feature related strings. See ``FeatureTypeTexts`` for more.
        """
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
    """:meta private:"""

    model = Person
    """:meta private:"""

    template_name = "persons/edit.html"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["available_person_types"] = self._get_available_person_types()

        return kwargs


class PersonCreateView(PersonCreateUpdateMixin, CreateView):
    """
    Creates a new :class:`persons.models.Person`.

    **Success redirection view**: :class:`persons.views.PersonIndexView`

    **Permissions**:

    Users that manage the created person's membership type.

    **Request body parameters:**

    *   ``first_name``
    *   ``last_name``
    *   ``person_type``
    *   ``sex``
    *   ``email``
    *   ``phone``
    *   ``date_of_birth``
    *   ``birth_number``
    *   ``health_insurance_company``
    *   ``city``
    *   ``postcode``
    *   ``street``
    *   ``swimming_time``
    """

    error_message = _("Nepodařilo se vytvořit novou osobu. Opravte chyby ve formuláři.")
    """:meta private:"""

    success_message = _("Osoba byla úspěšně vytvořena")
    """:meta private:"""


class PersonCreateChildView(PersonCreateUpdateMixin, CreateView):
    """
    Creates a new child :class:`persons.models.Person`.

    Allow for a simpler creation of children and their parents.

    **Success redirection view**: :class:`persons.views.PersonCreateChildParentView`

    **Permissions**:

    Users that manage the child person membership type.

    **Request body parameters:**

    *   ``first_name``
    *   ``last_name``
    *   ``person_type`` - must be "dite"
    *   ``sex``
    *   ``email``
    *   ``phone``
    *   ``date_of_birth``
    *   ``birth_number``
    *   ``health_insurance_company``
    *   ``city``
    *   ``postcode``
    *   ``street``
    *   ``swimming_time``
    """

    template_name = "persons/create_child.html"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["available_person_types"] = [Person.Type.CHILD]
        return kwargs

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:add-child-parent", kwargs={"pk": self.object.pk})


class PersonCreateChildParentView(PersonCreateUpdateMixin, CreateView):
    """
    Creates a new parent :class:`persons.models.Person`.

    Allow for a simpler creation of children and their parents.

    **Success redirection view**: :class:`persons.views.PersonCreateChildParentView`
    or :class:`persons.views.PersonDetailView` depending on the ``add_another_parent``
    parameter.

    **Permissions**:

    Users that manage the child person membership type.

    **Path parameters:**

    *   ``pk`` - the ID of the created parent's child

    **Request body parameters:**

    *   ``first_name``
    *   ``last_name``
    *   ``person_type``
    *   ``sex``
    *   ``email``
    *   ``phone``
    *   ``date_of_birth``
    *   ``birth_number``
    *   ``health_insurance_company``
    *   ``city``
    *   ``postcode``
    *   ``street``
    *   ``swimming_time``
    """

    template_name = "persons/create_child_parent.html"
    """:meta private:"""

    def __init__(self, **kwargs):
        """:meta private:"""

        super().__init__(**kwargs)
        self.child: Person

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.child = get_object_or_404(Person, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        *   ``child`` - the currently created parent's child
        *   ``parent_idx`` - the index of the currently created parent
            among the child's parents
        """
        kwargs.setdefault("child", self.child)
        kwargs.setdefault("parent_idx", self.child.managed_by.count() + 1)

        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["initial"] = {"person_type": Person.Type.PARENT.value}
        kwargs["is_add_child_parent_form"] = True

        return kwargs

    def form_valid(self, form):
        """:meta private:"""

        _ = super().form_valid(form)

        form.instance.managed_persons.add(self.child)

        if form.cleaned_data["add_another_parent"]:
            view = "persons:add-child-parent"
        else:
            view = "persons:detail"

        return HttpResponseRedirect(reverse(view, kwargs={"pk": self.child.pk}))


class PersonStatsView(PersonPermissionMixin, UpdateView):
    """
    Displays statistics of a person.

    **Permissions**:

    Users that manage the person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the person

    **Query parameters:**

    *   ``date_start`` - start date for the statistics
    *   ``date_end`` - end date for the statistics
    """

    form_class = PersonStatsForm
    """:meta private:"""

    http_method_names = ["get"]
    """:meta private:"""

    model = Person
    """:meta private:"""

    template_name = "persons/stats.html"
    """:meta private:"""

    def _get_parse_dates(self):
        """:meta private:"""

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
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["date_start"] = self.date_start
        kwargs["date_end"] = self.date_end

        return kwargs

    def _get_stats(self):
        """:meta private:"""

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
        """
        *   ``stats`` - the statistics
        """

        self.date_start, self.date_end = self._get_parse_dates()
        kwargs.setdefault("stats", self._get_stats())
        return super().get_context_data(**kwargs)


class PersonUpdateView(
    PersonPermissionQuerysetMixin, PersonCreateUpdateMixin, UpdateView
):
    """
    Edits an existing :class:`persons.models.Person`.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the edited person

    **Permissions**:

    Users that manage the edited person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the edited person

    **Request body parameters:**

    *   ``first_name``
    *   ``last_name``
    *   ``person_type``
    *   ``sex``
    *   ``email``
    *   ``phone``
    *   ``date_of_birth``
    *   ``birth_number``
    *   ``health_insurance_company``
    *   ``city``
    *   ``postcode``
    *   ``street``
    *   ``swimming_time``
    """

    error_message = _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
    """:meta private:"""

    success_message = _("Osoba byla úspěšně upravena")
    """:meta private:"""


class PersonDeleteView(
    PersonPermissionQuerysetMixin, PersonPermissionMixin, DeleteView
):
    """
    Deletes or anonymizes an existing :class:`persons.models.Person`.

    The person must not be a part of an upcoming event
    or have any borrowed equipment.

    Anonymization happens only if the person was part of a past event.

    **Success redirection view**: :class:`persons.views.PersonIndexView`

    **Permissions**:

    Users that manage the deleted person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the deleted person
    """

    model = Person
    """:meta private:"""

    success_message = _("Osoba byla úspěšně smazána")
    """:meta private:"""

    success_url = reverse_lazy("persons:index")
    """:meta private:"""

    template_name = "persons/delete.html"
    """:meta private:"""

    def form_valid(self, form):
        """:meta private:"""

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
        """:meta private:"""

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
        """:meta private:"""

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
    """:meta private:"""

    http_method_names = ["post"]
    """:meta private:"""

    model = Person
    """:meta private:"""

    def get_error_message(self, errors):
        """:meta private:"""

        return self.error_message + " ".join(errors["managed_person"])


class AddManagedPersonView(AddDeleteManagedPersonMixin):
    """
    Adds a person to a persons's managed persons.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the managing person

    **Permissions**:

    Users that manage the managing person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the managing person

    **Request body parameters:**

    *   ``managed_person`` - ID of the person to be added to managed persons
    """

    error_message = _("Nepodařilo se uložit novou spravovanou osobu. ")
    """:meta private:"""

    form_class = AddManagedPersonForm
    """:meta private:"""

    success_message = _("Nová spravovaná osoba byla přidána.")
    """:meta private:"""


class DeleteManagedPersonView(AddDeleteManagedPersonMixin):
    """
    Removes a person from a persons's managed persons.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the managing person

    **Permissions**:

    Users that manage the managing person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the managing person

    **Request body parameters:**

    *   ``managed_person`` - ID of the person to be removed from managed persons
    """

    error_message = _("Nepodařilo se odebrat spravovanou osobu. ")
    """:meta private:"""

    form_class = DeleteManagedPersonForm
    """:meta private:"""

    success_message = _("Odebrání spravované osoby bylo úspěšné.")
    """:meta private:"""


class EditHourlyRateView(PersonPermissionMixin, SuccessMessageMixin, UpdateView):
    """
    Edits the hourly rates of a person.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the managing person

    **Permissions**:

    Users that manage the managing person's membership type.

    **Path parameters:**

    *   ``pk`` - ID of the edited person
    """

    form_class = PersonHourlyRateForm
    """:meta private:"""

    model = Person
    """:meta private:"""

    success_message = _("Hodinové sazby byly úspěšně upraveny.")
    """:meta private:"""

    template_name = "persons/edit_hourly_rate.html"
    """:meta private:"""


class SelectedPersonsMixin(View):
    http_method_names = ["get"]
    """:meta private:"""

    def _get_queryset(self):
        """:meta private:"""

        raise NotImplementedError

    def _process_selected_persons(self, selected_persons):
        """:meta private:"""

        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        selected_persons = filter_queryset(
            PersonPermissionMixin.get_queryset_by_permission(
                self.request.user, self._get_queryset()
            ),
            request.GET,
            PersonsFilter,
        )

        return self._process_selected_persons(selected_persons)


class SendEmailToSelectedPersonsView(SelectedPersonsMixin):
    """
    Redirects to an open Gmail email with filtered persons
    and their managing persons set as recipients.

    Filters using :class:`PersonsFilter`.

    **Permissions**:

    Anyone.

    **Query parameters:**

    *   ``name``
    *   ``email``
    *   ``qualificationon``
    *   ``equipment``
    *   ``person_type``
    *   ``age_from``
    *   ``age_to``
    *   ``event_id``
    """

    def _get_queryset(self):
        """:meta private:"""

        return Person.objects.all()

    def _process_selected_persons(self, selected_persons):
        """:meta private:"""

        return send_email_to_selected_persons(selected_persons)


class ExportSelectedPersonsView(SelectedPersonsMixin):
    """
    Exports filtered persons as a CSV file.

    Filters using :class:`PersonsFilter`.

    **Permissions**:

    Anyone.

    **Query parameters:**

    *   ``name``
    *   ``email``
    *   ``qualificationon``
    *   ``equipment``
    *   ``person_type``
    *   ``age_from``
    *   ``age_to``
    *   ``event_id``
    """

    def _get_queryset(self):
        """:meta private:"""

        return Person.objects.with_age()

    def _process_selected_persons(self, selected_persons):
        """:meta private:"""

        return export_queryset_csv("vzs_osoby_export", selected_persons)


class MyProfileView(LoginRequiredMixin, DetailView):
    """
    Displays basic information about the active person.

    **Permissions**:

    Anyone.
    """

    model = Person
    """:meta private:"""

    template_name = "persons/my_profile.html"
    """:meta private:"""

    def get_object(self, queryset=None):
        """:meta private:"""

        return self.request.active_person

    def get_context_data(self, **kwargs):
        kwargs.setdefault("features_texts", FeatureTypeTexts)
        extend_kwargs_of_assignment_features(self.request.active_person, kwargs)

        return super().get_context_data(**kwargs)


class MyProfileUpdateView(LoginRequiredMixin, MessagesMixin, UpdateView):
    """
    Edits basic info about the active person.

    **Success redirection view**: :class:`persons.views.MyProfileView`

    **Permissions**:

    Anyone.

    **Query parameters:**

    *   ``email``
    *   ``phone``
    *   ``health_insurance_company``
    *   ``street``
    *   ``city``
    *   ``postcode``
    """

    error_message = _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
    """:meta private:"""

    form_class = MyProfileUpdateForm
    """:meta private:"""

    model = Person
    """:meta private:"""

    success_message = _("Váš profil byl úspěšně upraven.")
    """:meta private:"""

    success_url = reverse_lazy("my-profile:index")
    """:meta private:"""

    template_name = "persons/my_profile_edit.html"
    """:meta private:"""

    def get_object(self, queryset=None):
        """:meta private:"""

        return self.request.active_person
