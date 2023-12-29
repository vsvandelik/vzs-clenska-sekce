import datetime

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

from events.models import EventOrOccurrenceState
from trainings.models import TrainingOccurrence
from users.utils import get_permission_by_codename
from vzs import settings
from vzs.settings import TRAINING_CLOSE_DEADLINE_DAYS
from vzs.utils import get_server_url, date_pretty, send_notification_email


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
            coaches = set(unclosed_training.coaches.all())
            if unclosed_training.event.main_coach_assignment is not None:
                main_coach = unclosed_training.event.main_coach_assignment.person
                coaches.add(main_coach)

            url_address = get_server_url() + reverse(
                "trainings:fill-attendance",
                kwargs={
                    "event_id": unclosed_training.event.id,
                    "pk": unclosed_training.id,
                },
            )
            date = date_pretty(unclosed_training.datetime_start)
            send_notification_email(
                "Upozornění na neuzavřený trénink",
                f"Uzavřete trénink {unclosed_training.event} dne {date} na adrese {url_address}",
                coaches,
            )
            category_admins = [
                user.person
                for user in get_permission_by_codename(
                    unclosed_training.event.category
                ).user_set.all()
            ]
            send_notification_email(
                "Upozornění na neuzavřený trénink",
                f"Upozorňujeme Vás jako správce událostí druhu {unclosed_training.event.get_category_display()}, že trénink {unclosed_training.event.name} dne {date} na adrese {url_address} není uzavřen.",
                category_admins,
            )
