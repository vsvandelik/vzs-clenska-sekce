import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.urls import reverse

from events.models import EventOrOccurrenceState, Event
from one_time_events.models import OneTimeEventOccurrence
from users.utils import get_permission_by_codename
from vzs.settings import ONE_TIME_EVENT_CLOSE_DEADLINE_DAYS, CURRENT_DATETIME
from vzs.utils import get_server_url, send_notification_email


class Command(BaseCommand):
    help = "Send notification about unclosed one-time events."

    def handle(self, *args, **options):
        deadline = CURRENT_DATETIME() - datetime.timedelta(
            days=ONE_TIME_EVENT_CLOSE_DEADLINE_DAYS
        )
        unclosed_event_occurrences = OneTimeEventOccurrence.objects.filter(
            state=EventOrOccurrenceState.OPEN, event__date_end__lt=deadline
        )

        event_organizers = defaultdict(set)

        for unclosed_event_occurrence in unclosed_event_occurrences:
            notifications_receivers = set(unclosed_event_occurrence.organizers.all())
            event_organizers[unclosed_event_occurrence.event.id].update(
                notifications_receivers
            )

        for event_id, organizers in event_organizers.items():
            event = Event.objects.get(pk=event_id)

            url_address = get_server_url() + reverse(
                "one_time_events:detail", kwargs={"pk": event_id}
            )

            send_notification_email(
                "Upozornění na neuzavřenou událost",
                f"Uzavřete událost s názvem {event.name} na adrese {url_address}",
                organizers,
            )
            category_admins = get_permission_by_codename(event.category).user_set
            send_notification_email(
                "Upozornění na neuzavřenou událost",
                f"Upozorňujeme Vás jako správce událostí druhu {event.category.label}, že událost s názvem {event.name} na adrese {url_address} není uzavřena",
                category_admins,
            )
