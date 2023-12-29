from django.core.management import call_command


def unclosed_one_time_events_send_mails():
    call_command("check_unclosed_one_time_events")
