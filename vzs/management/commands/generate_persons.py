import random

from django.core.management.base import BaseCommand

from persons.models import Person


class Command(BaseCommand):
    help = "Creates N new persons to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int)

    def handle(self, *args, **options):
        for i in range(options["N"]):
            new_person = Person(
                email=f"email.osoba.{i}@email.cz",
                first_name=f"Testovaci",
                last_name=f"Osoba {i}",
                sex=random.choices(Person.Sex.values)[0],
                person_type=random.choices(Person.Type.values)[0],
            )
            new_person.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new persons.')
        )
