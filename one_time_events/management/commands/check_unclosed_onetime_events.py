import datetime
from collections import defaultdict

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

from events.models import EventOrOccurrenceState, Event
from one_time_events.models import OneTimeEventOccurrence
from vzs import settings
from vzs.settings import ONETIME_EVENT_CLOSE_DEADLINE_DAYS
from vzs.utils import get_server_url


class Command(BaseCommand):
    help = "Send notification about unclosed one-time events."

    def handle(self, *args, **options):
        deadline = datetime.datetime.now() - datetime.timedelta(
            days=ONETIME_EVENT_CLOSE_DEADLINE_DAYS
        )
        unclosed_event_occurrences = OneTimeEventOccurrence.objects.filter(
            state=EventOrOccurrenceState.OPEN, event__date_end__lt=deadline
        )

        event_organizers = defaultdict(set)

        for unclosed_event_occurrence in unclosed_event_occurrences:
            notifications_receivers = set(
                unclosed_event_occurrence.organizers.values_list("email", flat=True)
            )
            event_organizers[unclosed_event_occurrence.event.id].update(
                notifications_receivers
            )

        for event_id, organizers in event_organizers.items():
            event = Event.objects.get(pk=event_id)

            url_address = get_server_url() + reverse(
                "one_time_events:detail", kwargs={"pk": event_id}
            )

            send_mail(
                "Upozornění na neuzavřenou akci",
                f"Uzavřete akci s názvem {event.name} na adrese {url_address}.",
                settings.ADMIN_EMAIL,
                [organizers],
                fail_silently=False,
            )

        # TODO: send notification only to main organizer of the event
        # TODO: send cc of notification to admin of the event category
