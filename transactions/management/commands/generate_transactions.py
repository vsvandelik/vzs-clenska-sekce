from datetime import date
from random import choice as random_choice
from random import randint

from django.core.management.base import BaseCommand

from persons.models import Person
from transactions.models import Transaction


class Command(BaseCommand):
    help = "Creates N new transactions to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int)

    def handle(self, *args, **options):
        persons = list(Person.objects.all())

        count = options["N"]

        Transaction.objects.bulk_create(
            Transaction(
                person=random_choice(persons),
                amount=randint(-200, 200),
                reason=f"Popis{i}",
                date_due=date(2024, 1, randint(1, 31)),
            )
            for i in range(count)
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new transactions.')
        )
