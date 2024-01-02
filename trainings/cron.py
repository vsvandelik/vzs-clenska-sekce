from django.core.management import call_command


def unclosed_trainings_send_mails():
    call_command("check_unclosed_trainings")
