import csv
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from persons.models import Person


class Command(BaseCommand):
    help = "Convert csv file with users from old system to json data which can be load to new system via `python manage.py loaddata` command."

    def __init__(self):
        super().__init__()
        self.persons = []

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str)

    def handle(self, *args, **options):
        with open(options["filename"], "r") as f:
            reader = csv.reader(f)

            header = {name: idx for idx, name in enumerate(next(reader))}

            for idx, row in enumerate(reader, start=2):
                self._process_single_person_row(header, row, idx)

        self.stdout.write(self.style.SUCCESS(f"Successfully created"))

    def _check_if_person_already_exists(self, person: Person):
        found_weak_duplicate = False
        for p in self.persons:
            if p.first_name == person.first_name and p.last_name == person.last_name:
                if p.email == person.email or p.phone == person.phone:
                    return p
                else:
                    found_weak_duplicate = True

        return found_weak_duplicate

    def _return_if_not_duplicate(self, person: Person):
        possible_existing_person = self._check_if_person_already_exists(person)
        if isinstance(possible_existing_person, Person):
            return possible_existing_person
        elif possible_existing_person is True:
            self.stdout.write(
                self.style.WARNING(
                    f"There is already person with name {person.first_name} {person.last_name} in the list. Adjust contact info if the person is the same."
                )
            )

        self.persons.append(person)

        return person

    def _process_single_person_row(self, header: dict, row: list, line: int):
        get_val = lambda key: self._clean_value(key, row[header[key]])

        try:
            person = self._process_person(get_val)
            person.parents = []

            parent1 = self._process_parent(get_val, 1)
            if parent1:
                person.parents.append(parent1)

            parent2 = self._process_parent(get_val, 2)
            if parent2:
                person.parents.append(parent2)

        except ValidationError as e:
            self._print_errors_as_warnings(e.message_dict, line)
        except ValueError as e:
            self.stdout.write(self.style.WARNING(f"Error in line {line}: {e}"))

    def _process_person(self, get_val):
        first_name = get_val("jmeno")
        last_name = get_val("prijmeni")
        if not first_name or not last_name:
            raise ValidationError({"name": "There is no name. Skipping."})

        person = Person(
            email=get_val("mail"),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=get_val("narozeni"),
            sex=Person.Sex.M,  # TODO: fix
            person_type=Person.Type.ADULT,  # TODO: fix
            birth_number=get_val("rc"),
            health_insurance_company=self._process_pojistovna(
                get_val("Zdravotni_pojistovna"), get_val("zp")
            ),
            phone=get_val("telefon"),
            street=get_val("ulice"),
            city=get_val("mesto"),
            postcode=get_val("psc"),
        )
        person.clean_fields()

        return self._return_if_not_duplicate(person)

    def _process_parent(self, get_val, parent_idx: int):
        first_name = get_val(f"jmeno{parent_idx}")
        last_name = get_val(f"prijmeni{parent_idx}")
        email = get_val(f"mail{parent_idx}")
        phone = get_val(f"telefon{parent_idx}")

        if not first_name and not last_name and not email and not phone:
            return None
        elif not first_name and not last_name:
            raise ValidationError(
                {
                    f"parent{parent_idx}": "There is no name, only contact information. Skipping."
                }
            )

        parent = Person(
            email=email,
            first_name=first_name,
            last_name=last_name,
            sex=Person.Sex.M,  # TODO: fix
            person_type=Person.Type.PARENT,
            phone=phone,
        )
        parent.clean_fields()

        return self._return_if_not_duplicate(parent)

    def _print_errors_as_warnings(self, errors, line):
        for field, error in errors.items():
            error_message = " ".join(error) if isinstance(error, list) else error
            self.stdout.write(
                self.style.WARNING(f"Error in line {line}: {field}: {error_message}")
            )

    def _clean_value(self, key: str, value: str) -> Any | None:
        value_processor = getattr(self, f"_process_{key}", None)

        value = (
            value.strip()
            if value and value != "NULL" and value.replace("?", "") != ""
            else None
        )

        if value_processor and callable(value_processor) and value is not None:
            return value_processor(value)
        else:
            return value

    def _process_narozeni(self, value: str) -> str:
        value = value.replace(" ", "").replace(",", ".")
        input_date = datetime.strptime(value, "%d.%m.%Y")
        return input_date.strftime("%Y-%m-%d")

    def _process_psc(self, value: str) -> int:
        return int(value.replace(" ", ""))

    def _process_pojistovna(self, value1: str, value2: str) -> str | None:
        value1 = self._process_health_insurance_company_parser(value1)
        value2 = self._process_health_insurance_company_parser(value2)

        if not value1 and not value2:
            return None
        if not value1:
            return self._process_health_insurance_company_parser(value2)
        elif not value2 or value1 == value2:
            return self._process_health_insurance_company_parser(value1)
        else:
            raise ValidationError(
                {
                    "health_insurance_company": f"Two different health insurance companies: {value1} and {value2}"
                }
            )

    def _process_health_insurance_company_parser(self, value):
        if not value:
            return None

        digits_only = "".join(c for c in value if c.isdigit())

        if digits_only and int(digits_only) == 0:
            return None

        if digits_only in Person.HealthInsuranceCompany.values:
            return digits_only

        letters_only = "".join(c for c in value.upper() if c.isalpha())
        if hasattr(Person.HealthInsuranceCompany, letters_only):
            return getattr(Person.HealthInsuranceCompany, letters_only)

        return value
