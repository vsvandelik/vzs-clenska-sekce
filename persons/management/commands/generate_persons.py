from random import choice as random_choice
from random import randint

from django.core.management.base import BaseCommand
from django.utils.timezone import localdate, timedelta

from persons.models import Person
from vzs.settings import CURRENT_DATETIME


class Command(BaseCommand):
    help = "Creates N new persons to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int)

    def handle(self, *args, **options):
        count = options["N"]

        Person.objects.bulk_create(
            Person(
                email=f"email.osoba.{i}@email.cz",
                first_name=f"Testovaci",
                last_name=f"Osoba {i}",
                date_of_birth=localdate(
                    CURRENT_DATETIME()
                    - timedelta(weeks=randint(5, 50) * 52 + randint(0, 365))
                ),
                sex=random_choice(Person.Sex.values),
                person_type=random_choice(Person.Type.values),
            )
            for i in range(count)
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {count} new persons.")
        )
