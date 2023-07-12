import zoneinfo

from django.utils import timezone


def _date_prague(date):
    return timezone.localdate(date, timezone=zoneinfo.ZoneInfo("Europe/Prague"))
