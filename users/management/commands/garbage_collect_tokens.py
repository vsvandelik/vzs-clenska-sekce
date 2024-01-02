from django.core.management.base import BaseCommand

from users.models import ResetPasswordToken


class Command(BaseCommand):
    help = "Garbage collects old reset password tokens."

    def handle(self, *args, **options):
        ResetPasswordToken.objects.filter(ResetPasswordToken.has_expired).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted old reset password tokens.")
        )
