from transactions.models import Transaction
from persons.models import Person

from django.core.management.base import BaseCommand

import random
from datetime import date


class Command(BaseCommand):
    help = "Creates N new transactions to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int)

    def handle(self, *args, **options):
        persons = list(Person.objects.all())
        transactions = []

        for i in range(options["N"]):
            transactions.append(
                Transaction(
                    person=random.choice(persons),
                    amount=random.randint(-200, 200),
                    reason=f"Popis{i}",
                    date_due=date(2024, 1, random.randint(1, 31)),
                )
            )

        Transaction.objects.bulk_create(transactions)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new transactions.')
        )
