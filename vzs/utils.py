import csv
import zoneinfo
from urllib import parse

from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from vzs import settings


def _date_prague(date):
    return timezone.localdate(date, timezone=zoneinfo.ZoneInfo("Europe/Prague"))


def export_queryset_csv(filename, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
    response.write("\ufeff".encode("utf8"))

    writer = csv.writer(response, delimiter=";")

    writer.writerow(queryset.model.csv_header())

    for instance in queryset:
        writer.writerow(instance.csv_row())

    return response


def reverse_with_get_params(*args, **kwargs):
    get_params = kwargs.pop("get", {})
    url = reverse(*args, **kwargs)
    if get_params:
        url += "?" + parse.urlencode(get_params)
    return url


def get_server_url():
    return f"{settings.SERVER_PROTOCOL}://{settings.SERVER_DOMAIN}"
