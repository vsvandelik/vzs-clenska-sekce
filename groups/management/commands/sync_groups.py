from django.core.management.base import BaseCommand

from groups.models import Group
from groups.utils import sync_single_group_with_google


class Command(BaseCommand):
    help = "Synchronize local groups with Google Workplace's groups"

    def add_arguments(self, parser):
        parser.add_argument("group_id", nargs="?", type=int)

    def handle(self, *args, **options):
        if options["group_id"]:
            try:
                group_instance = Group.objects.get(pk=options["group_id"])
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR("Cannot find a group instance to synchronize")
                )
                return

            if not group_instance.google_email:
                self.stdout.write(
                    self.style.ERROR(
                        "Selected group does not have google e-mail address defined"
                    )
                )
                return

            sync_single_group_with_google(group_instance)
            self.stdout.write(
                self.style.ERROR("Successfully synchronized group %s")
                % group_instance.name
            )

        else:
            for group in Group.objects.filter(google_email__isnull=False):
                sync_single_group_with_google(group)

            self.stdout.write(self.style.ERROR("Successfully synchronized all groups"))
