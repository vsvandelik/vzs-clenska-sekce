from django.core.management import call_command


def garbage_collect_tokens():
    call_command("garbage_collect_tokens")
