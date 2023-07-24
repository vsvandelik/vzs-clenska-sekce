import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from price_lists.models import PriceList, PriceListBonus
from features.models import Feature


def lower_bounded_int(value, lower_bound):
    v = int(value)
    if v < lower_bound:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def positive_int(value):
    return lower_bounded_int(value, 1)


def non_negative_int(value):
    return lower_bounded_int(value, 0)


class Command(BaseCommand):
    help = "Creates N new price_lists to test design with."

    def add_arguments(self, parser):
        parser.add_argument(
            "N", type=positive_int, help="the number of price_lists to create"
        )
        parser.add_argument(
            "-b",
            "--bonus-count",
            type=non_negative_int,
            help="the number of bonuses to add to price_list (won't be fulfilled if there is not enough qualifications)",
        )
        parser.add_argument(
            "-s",
            "--salary-base",
            type=non_negative_int,
            help="the salary base for organizers for running the event",
        )
        parser.add_argument(
            "-p",
            "--participant-fee",
            type=non_negative_int,
            help="the fee payed by participants for attending the event",
        )

    def handle(self, *args, **options):
        idx = PriceList.objects.all().count() + 1
        qualifications = Feature.qualifications.all()
        qualifications_length = qualifications.count()
        if options["bonus_count"] is not None:
            bonuses_to_add = min(options["bonus_count"], qualifications_length)
            if bonuses_to_add < options["bonus_count"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"Limiting bonus_count to {bonuses_to_add} due to insufficient number of qualifications"
                    )
                )
        price_lists = []
        bonuses = []
        for i in range(options["N"]):
            if not options["bonus_count"] is not None:
                bonuses_to_add = random.randint(0, qualifications_length)

            salary_base = options["salary_base"] or random.randint(0, 10000)
            participant_fee = options["participant_fee"] or random.randint(0, 10000)

            price_list = PriceList(
                name=f"ceník_{idx}",
                salary_base=salary_base,
                participant_fee=participant_fee,
                is_template=True,
            )
            price_lists.append(price_list)

            bonus_qualifications = random.sample(list(qualifications), k=bonuses_to_add)
            for q in bonus_qualifications:
                bonus = PriceListBonus(
                    price_list=price_list,
                    feature=q,
                    extra_salary=random.randint(0, 1000),
                )
                bonuses.append(bonus)

            idx += 1

        PriceList.objects.bulk_create(price_lists)
        PriceListBonus.objects.bulk_create(bonuses)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new price_lists.')
        )
