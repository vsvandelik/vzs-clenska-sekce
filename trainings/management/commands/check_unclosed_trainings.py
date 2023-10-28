import datetime

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

from events.models import EventOrOccurrenceState
from trainings.models import TrainingOccurrence
from vzs import settings
from vzs.settings import TRAINING_CLOSE_DEADLINE_DAYS
from vzs.utils import get_server_url


class Command(BaseCommand):
    help = "Send notification about unclosed trainings."

    def handle(self, *args, **options):
        deadline = datetime.datetime.now() - datetime.timedelta(
            days=TRAINING_CLOSE_DEADLINE_DAYS
        )
        unclosed_trainings = TrainingOccurrence.objects.filter(
            state=EventOrOccurrenceState.OPEN, datetime_end__lt=deadline
        )

        for unclosed_training in unclosed_trainings:
            coaches_emails = set(
                unclosed_training.coaches.values_list("email", flat=True)
            )
            if unclosed_training.event.main_coach_assignment:
                main_coach = unclosed_training.event.main_coach_assignment.person
                coaches_emails.add(main_coach.email)

            url_address = get_server_url() + reverse(
                "trainings:fill-attendance",
                kwargs={
                    "event_id": unclosed_training.event.id,
                    "pk": unclosed_training.id,
                },
            )

            send_mail(
                "Upozornění na neuzavřený trénink",
                f"Uzavřete trénink dne {url_address}.",
                settings.ADMIN_EMAIL,
                [coaches_emails],
                fail_silently=False,
            )

        # TODO: send cc of notification to admin of the event category
