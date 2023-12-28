from django.core.management import call_command


def features_expiry_send_mails():
    call_command("send_feature_expiry_mail")
