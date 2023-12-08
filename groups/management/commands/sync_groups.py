from django.core.management.base import BaseCommand

from groups.models import Group
from groups.utils import sync_single_group_with_google


class Command(BaseCommand):
    help = "Synchronize local groups with Google Workplace's groups."

    def add_arguments(self, parser):
        parser.add_argument("group_id", nargs="?", type=int)

    def _handle_single(self, group_id):
        group = Group.objects.filter(pk=group_id).first()

        if group is None:
            self.stdout.write(
                self.style.ERROR("Could not find a group instance to synchronize.")
            )
            return

        if group.google_email is None:
            self.stdout.write(
                self.style.ERROR(
                    "Selected group does not have Google email address defined."
                )
            )
            return

        sync_single_group_with_google(group)

        self.stdout.write(
            self.style.SUCCESS("Successfully synchronized group {}.").format(group.name)
        )

    def _handle_all(self):
        for group in Group.objects.filter(google_email__isnull=False):
            sync_single_group_with_google(group)

        self.stdout.write(self.style.SUCCESS("Successfully synchronized all groups."))

    def handle(self, group_id, **options):
        if group_id is not None:
            self._handle_single(group_id)
        else:
            self._handle_all()
