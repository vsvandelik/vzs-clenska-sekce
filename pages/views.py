from datetime import timedelta

from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from features.models import Feature, FeatureAssignment
from one_time_events.models import OneTimeEvent
from pages.forms import PageEditForm
from pages.models import Page
from trainings.models import TrainingOccurrence
from transactions.models import Transaction
from users.permissions import LoginRequiredMixin, PermissionRequiredMixin
from vzs.utils import today


class HomeView(LoginRequiredMixin, TemplateView):
    """
    Displays the home page.

    Contains a dashboard with various information about the active person.
    See :meth:`get_context_data` for more information.

    If there is no information to display, logo of the Organization is shown instead.
    """

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        """
        *   ``multiple_managed_people``: whether the active person
            manages more than one person
        *   ``unsettled_transactions``: unsettled transactions of the active person
        *   ``soon_expiring_qualifications``: qualifications of the active person
            that expire in 90 days or less
        *   ``soon_returning_equipment``: equipment of the active person that
            has to be returned in 30 days or less
        *   ``upcoming_trainings_participant``: upcoming trainings where the active
            person is a participant
        *   ``upcoming_trainings_coach``: upcoming trainings where the active
            person is a coach
        *   ``upcoming_onetimeevents_participant``: upcoming one-time events where
            the active person is a participant
        *   ``upcoming_onetimeevents_organizer``: upcoming one-time events where
            the active person is an organizer
        """

        active_person = self.request.active_person

        kwargs.setdefault(
            "multiple_managed_people",
            len(self.request.user.person.get_managed_persons()) > 1,
        )
        kwargs.setdefault("unsettled_transactions", self._get_unsettled_transactions())
        kwargs.setdefault(
            "soon_expiring_qualifications",
            self._get_soon_expiring_features(Feature.Type.QUALIFICATION, 90),
        )
        kwargs.setdefault(
            "soon_returning_equipment",
            self._get_soon_expiring_features(Feature.Type.EQUIPMENT, 30),
        )

        kwargs.setdefault(
            "upcoming_trainings_participant",
            TrainingOccurrence.get_upcoming_by_participant(active_person).all()[:5],
        )
        kwargs.setdefault(
            "upcoming_trainings_coach",
            TrainingOccurrence.get_upcoming_by_coach(active_person).all()[:5],
        )

        kwargs.setdefault(
            "upcoming_onetimeevents_participant",
            OneTimeEvent.get_upcoming_by_participant(active_person).all()[:5],
        )
        kwargs.setdefault(
            "upcoming_onetimeevents_organizer",
            OneTimeEvent.get_upcoming_by_organizer(active_person).all()[:5],
        )

        return super().get_context_data(**kwargs)

    def _get_unsettled_transactions(self):
        """:meta private:"""

        return Transaction.objects.filter(
            person=self.request.active_person,
            fio_transaction__isnull=True,
            amount__lt=0,
        ).all()

    def _get_soon_expiring_features(self, feature_type, days):
        """:meta private:"""

        return FeatureAssignment.objects.filter(
            person=self.request.active_person,
            feature__feature_type=feature_type,
            date_expire__lte=today() + timedelta(days=days),
            date_returned__isnull=True,
        ).all()


class PageDetailView(LoginRequiredMixin, DetailView):
    """
    Displays an editable page.

    Shows an edit button to users with ``stranky`` permission.

    **Path parameters**:

    *   ``slug`` - page slug
    """

    model = Page
    template_name = "pages/detail.html"


class PageEditView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Edits a page.

    Slug can be changed, therefore the URL of the page can change.

    **Success redirection view**: :class:`PageDetailView` of the edited page.

    **Permissions**:

    Users with ``stranky`` permission.

    **Path parameters**:

    *   ``slug`` - page slug

    **Request body parameters**:

    *   ``title``
    *   ``content``
    *   ``slug``
    """

    form_class = PageEditForm
    model = Page
    permissions_formula = [["stranky"]]
    success_message = _("Stránka byla úspěšně upravena.")
    template_name = "pages/edit.html"


class ErrorPage400View(TemplateView):
    template_name = "pages/errors/400.html"


class ErrorPage403View(TemplateView):
    template_name = "pages/errors/403.html"


class ErrorPage404View(TemplateView):
    template_name = "pages/errors/404.html"


class ErrorPage500View(TemplateView):
    template_name = "pages/errors/500.html"
