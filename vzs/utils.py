import csv
import unicodedata
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, TypedDict, TypeVar, get_type_hints
from urllib import parse
from urllib.parse import quote

from django.core.mail import send_mail
from django.db.models import Model
from django.db.models.query import Q, QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import formats
from django.utils.timezone import localdate, make_aware

from vzs import settings
from vzs.settings import CURRENT_DATETIME


def export_queryset_csv(filename, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": rfc5987_content_disposition(f"{filename}.csv")},
    )
    response.write("\ufeff".encode("utf8"))

    writer = csv.writer(response, delimiter=";")

    writer.writerow(queryset.model.csv_header())

    for instance in queryset:
        writer.writerow(instance.csv_row())

    return response


def rfc5987_content_disposition(file_name):
    ascii_name = (
        unicodedata.normalize("NFKD", file_name).encode("ascii", "ignore").decode()
    )
    header = f'attachment; filename="{ascii_name}"'
    if ascii_name != file_name:
        quoted_name = quote(file_name)
        header += "; filename*=UTF-8''{}".format(quoted_name)

    return header


def reverse_with_get_params(*args, **kwargs):
    get_params = kwargs.pop("get", {})
    url = reverse(*args, **kwargs)
    if get_params:
        url += "?" + parse.urlencode(get_params)
    return url


def send_notification_email(subject, message, persons_list, *args, **kwargs):
    recipient_set = set()
    for person in persons_list:
        for recipient in email_notification_recipient_set(person):
            recipient_set.add(recipient)

    send_mail(
        message,
        subject,
        settings.NOTIFICATION_SENDER_EMAIL,
        list(recipient_set),
        *args,
        **kwargs,
    )


def email_notification_recipient_set(person):
    emails = set()

    if person.email is not None:
        emails.add(person.email)

    persons_managing = person.managed_by.all()
    for person_managing in persons_managing:
        if person_managing.email is not None:
            emails.add(person_managing.email)
    return emails


def date_pretty(value):
    return formats.date_format(value, settings.cs_formats.DATE_FORMAT)


def time_pretty(value):
    return formats.time_format(value, settings.cs_formats.TIME_FORMAT)


def payment_email_html(transaction, request):
    amount = abs(transaction.amount)

    qr_uri = request.build_absolute_uri(
        reverse("transactions:qr", args=(transaction.pk,))
    )

    qr_link = f'<a href="{qr_uri}">{qr_uri}</a>'

    return (
        f"Prosím proveďte platbu:<ul>"
        f"<li>Číslo účtu: {settings.FIO_ACCOUNT_PRETTY}</li>"
        f"<li>Částka: {amount} Kč</li>"
        f"<li>Variabilní symbol: {transaction.id}</li>"
        f"<li>Datum splatnosti: {date_pretty(transaction.date_due)}</li></ul>"
        f'{qr_html_image(transaction, "QR platba")}'
        f"<p>Informace o této platbě naleznete v IS, odkaz: {qr_link}</p>"
    )


def qr(transaction):
    return (
        f"http://api.paylibo.com/paylibo/generator/czech/image"
        f"?currency=CZK"
        f"&accountNumber={settings.FIO_ACCOUNT_NUMBER}"
        f"&bankCode={settings.FIO_BANK_NUMBER}"
        f"&amount={abs(transaction.amount)}"
        f"&vs={transaction.pk}"
    )


def qr_html_image(transaction, alt_text=None):
    if alt_text is not None:
        alt_text = f'alt="{alt_text}"'
    qr_img_src = qr(transaction)
    return f'<img src="{qr_img_src}" {alt_text}>'


Q_TRUE = ~Q(pk__in=[])
"""
TRUE constant, evaluates as true for any instance
"""


T = TypeVar("T", bound=Model)


def filter_queryset(
    queryset: QuerySet[T], data: Mapping[str, Any] | None, Filter: type[TypedDict]
) -> QuerySet[T]:
    """
    Filters ``queryset`` with a ``Q`` object constructed from the ``data`` mapping.

    ``Filter`` defines the filter. It inherits from :class:`typing.TypedDict`
    and provides transformations using :class:`typing.Annotated`.

    Transformation is a function that takes the value from the ``data`` mapping
    and returns a ``Q`` object.

    Applies transformations to all fields of the mapping specified by ``Filter``
    and compounds the resulting `Q`` objects using logical AND.

    Values from ``data`` are converted to the type specified by ``Filter``.

    Missing values and empty strings are ignored.

    If ``data`` is ``None``, returns ``queryset`` unchanged.

    Example: ::

        class Filter(TypedDict, total=False):
            field: Annotated[T, lambda value: Q(name=value)]
    """

    if data is None:
        return queryset

    filter = Q_TRUE

    # iterates over the fields of ``Filter``
    for key, annotated in get_type_hints(Filter, include_extras=True).items():
        value = data.get(key)

        if value is not None and value != "":
            # gets the first Annotated metadata value
            transform: Callable[[Any], Q] = annotated.__metadata__[0]

            type = annotated.__args__[0]

            if not isinstance(value, type):
                value = type(value)

            filter &= transform(value)

    return queryset.filter(filter)


def combine_date_and_time(date, time):
    return make_aware(datetime.combine(date, time))


def today():
    return localdate(CURRENT_DATETIME())


def get_server_url():
    return f"{settings.SERVER_PROTOCOL}://{settings.SERVER_DOMAIN}"
