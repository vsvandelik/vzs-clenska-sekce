from datetime import timedelta

from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from features.models import FeatureAssignment, Feature
from one_time_events.models import OneTimeEvent
from pages.forms import PageEditForm
from pages.models import Page
from trainings.models import TrainingOccurrence
from transactions.models import Transaction
from users.permissions import PermissionRequiredMixin, LoginRequiredMixin
from vzs.utils import today


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
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

        print(today())

        return super().get_context_data(**kwargs)

    def _get_unsettled_transactions(self):
        return Transaction.objects.filter(
            person=self.request.active_person,
            fio_transaction__isnull=True,
            amount__lt=0,
        ).all()

    def _get_soon_expiring_features(self, feature_type, days):
        return FeatureAssignment.objects.filter(
            person=self.request.active_person,
            feature__feature_type=feature_type,
            date_expire__lte=today() + timedelta(days=days),
            date_returned__isnull=True,
        ).all()


class PageDetailView(LoginRequiredMixin, DetailView):
    model = Page
    template_name = "pages/detail.html"


class PageEditView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
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
