from random import choice as random_choice
from random import randint
from sys import stderr

from django.core.management.base import BaseCommand
from django.utils.timezone import localdate, timedelta

from persons.models import Person
from users.models import User
from vzs.settings import CURRENT_DATETIME


class Command(BaseCommand):
    help = "Creates N new persons to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int)

    def handle(self, *args, **options):
        count = options["N"]

        persons = Person.objects.bulk_create(
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

        users = User.objects.bulk_create(User(person=person) for person in persons)

        for user in users:
            user.set_unusable_password()
            user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {count} new persons.")
        )
