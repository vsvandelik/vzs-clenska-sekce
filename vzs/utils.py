import csv
import zoneinfo
from urllib import parse

from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone, formats

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

    return f'Prosím proveďte platbu:<ul><li>Číslo účtu: {settings.FIO_ACCOUNT_PRETTY}</li><li>Částka: {amount} Kč</li><li>Variabilní symbol: {transaction.id}</li><li>Datum splatnosti: {date_pretty(transaction.date_due)}</li></ul>{qr_html_image(transaction, "QR platba")}<p>Informace o této platbě naleznete v IS, odkaz: {qr_link}</p>'


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
