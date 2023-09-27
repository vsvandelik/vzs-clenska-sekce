from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import ResetPasswordToken
from vzs import settings


class Command(BaseCommand):
    help = "Garbage collects old reset password tokens."

    def handle(self, *args, **options):
        ResetPasswordToken.objects.filter(ResetPasswordToken.has_expired).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted old reset password tokens.")
        )
