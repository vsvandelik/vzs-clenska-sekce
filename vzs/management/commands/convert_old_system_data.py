import csv
import os
import pickle
from datetime import datetime
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from genderize import Genderize

from persons.models import Person
from vzs.utils import today


class Command(BaseCommand):
    help = "Convert csv file with users from old system to json data which can be load to new system via `python manage.py loaddata` command."

    def __init__(self):
        super().__init__()
        self.input_processor = InputProcessor(self.stderr, self.style)
        self.output_printer = OutputPrinter(self.stdout, self.style)

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str)

        parser.add_argument("--genderize_api_key", type=str, default=None)
        parser.add_argument("--genderize_file_path", type=str, default="data/genderize")
        parser.add_argument("--genderize_batch_size", type=int, default=10)

    def handle(self, *args, **options):
        genderize_settings = {
            "genderize_api_key": options["genderize_api_key"],
            "genderize_file_path": options["genderize_file_path"],
            "genderize_batch_size": options["genderize_batch_size"],
        }

        persons = self.input_processor.process_input(
            options["filename"], genderize_settings
        )

        self.output_printer.print_output(persons)


class InputProcessor:
    def __init__(self, stderr, style):
        super().__init__()
        self.persons = []
        self.stderr = stderr
        self.style = style

    def process_input(self, filename, genderize_settings):
        with open(filename, "r") as f:
            reader = csv.reader(f)

            header = {name: idx for idx, name in enumerate(next(reader))}

            for idx, row in enumerate(reader, start=2):
                self._process_single_person_row(header, row, idx)

            if genderize_settings["genderize_api_key"]:
                self._fix_sex_with_genderize(genderize_settings)

        return self.persons

    def _process_single_person_row(self, header: dict, row: list, line: int):
        get_val = lambda key: InputFieldsCleaner.clean_value(key, row[header[key]])

        try:
            password = self._get_user_account_password(get_val)

            person = self._process_person(get_val)
            person.password = password
            person_idx = self.persons.index(person)

            for parent_idx in range(1, 3):
                parent = self._process_parent(get_val, parent_idx)
                if parent:
                    parent.managing_persons.append(person_idx)
                    parent.password = password

        except ValidationError as e:
            self._print_errors_as_warnings(e.message_dict, line)
        except ValueError as e:
            self.stderr.write(self.style.WARNING(f"Error in line {line}: {e}"))

    def _process_person(self, get_val):
        first_name = get_val("jmeno")
        last_name = get_val("prijmeni")
        if not first_name or not last_name:
            raise ValidationError({"name": "There is no name. Skipping."})

        birth_number = get_val("rc")
        date_of_birth = get_val("narozeni")
        sex = InputFieldsCleaner.process_sex_by_birth_number(birth_number)

        person = Person(
            email=get_val("mail"),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex=sex or Person.Sex.UNKNOWN,
            person_type=InputFieldsCleaner.process_type_by_date_of_birth(date_of_birth),
            birth_number=birth_number,
            health_insurance_company=InputFieldsCleaner.process_pojistovna(
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
            sex=Person.Sex.UNKNOWN,
            person_type=Person.Type.PARENT,
            phone=phone,
        )
        parent.clean_fields()

        return self._return_if_not_duplicate(parent)

    def _check_if_person_already_exists(self, person: Person):
        found_weak_duplicate = False
        for p in self.persons:
            if p.first_name == person.first_name and p.last_name == person.last_name:
                if p.email == person.email or p.phone == person.phone:
                    return p
                else:
                    found_weak_duplicate = True
            elif p.email == person.email:
                person.email = None
                raise ValidationError(
                    {
                        "email": f"E-mailová adresa {p.email} již byla použita u osoby s jiným jménem ({p.name}). Osoba se vynechává."
                    }
                )

        return found_weak_duplicate

    def _return_if_not_duplicate(self, person: Person):
        possible_existing_person = self._check_if_person_already_exists(person)
        if isinstance(possible_existing_person, Person):
            return possible_existing_person
        elif possible_existing_person is True:
            self.stderr.write(
                self.style.WARNING(
                    f"There is already person with name {person.first_name} {person.last_name} in the list. Adjust contact info if the person is the same."
                )
            )

        person.managing_persons = []
        self.persons.append(person)

        return person

    def _get_user_account_password(self, get_val):
        username = get_val("login")
        password = get_val("heslo")
        if not username or not password:
            return None

        return make_password(password)

    def _print_errors_as_warnings(self, errors, line):
        for field, error in errors.items():
            error_message = " ".join(error) if isinstance(error, list) else error
            self.stderr.write(
                self.style.WARNING(f"Error in line {line}: {field}: {error_message}")
            )

    def _fix_sex_with_genderize(self):
        persons_to_fix = [p for p in self.persons if p.sex == Person.Sex.UNKNOWN]
        names = set(p.first_name for p in persons_to_fix)

        sex_by_names = self._get_sex_by_names(names, genderize_settings)

        for person in persons_to_fix:
            if person.first_name in sex_by_names:
                person.sex = sex_by_names[person.first_name]

    def _get_sex_by_names(self, names, genderize_settings):
        cache_path = genderize_settings["genderize_file_path"]
        batch_size = genderize_settings["genderize_batch_size"]

        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                sex_by_names = pickle.load(f)
        else:
            sex_by_names = {}

        missing_names = list(names.difference(set(sex_by_names.keys())))

        if len(missing_names) == 0:
            return sex_by_names

        returned_gender_count = 0
        genderize = Genderize(api_key=genderize_settings["genderize_api_key"])

        for i in range(0, len(missing_names), batch_size):
            subset_names = missing_names[i : i + batch_size]
            self.stderr.write(
                self.style.SUCCESS(f"Batch {i} with {len(subset_names)} names.")
            )
            data = genderize.get(names=subset_names, country_id="cz", language_id="cs")

            for d in data:
                name = d["name"]
                if d["gender"] == "female":
                    sex_by_names[name] = Person.Sex.F
                else:
                    sex_by_names[name] = Person.Sex.M

                if d["gender"] is not None:
                    returned_gender_count += 1

        with open(cache_path, "wb") as f:
            pickle.dump(sex_by_names, f)

        self.stderr.write(
            self.style.SUCCESS(
                f"Genderize.io API was called for {len(missing_names)} names and returned gender for {returned_gender_count} names."
            )
        )

        return sex_by_names


class InputFieldsCleaner:
    @staticmethod
    def clean_value(key: str, value: str) -> Any | None:
        value_processor = getattr(InputFieldsCleaner, f"process_{key}", None)

        value = (
            value.strip()
            if value and value != "NULL" and value.replace("?", "") != ""
            else None
        )

        if value_processor and callable(value_processor) and value is not None:
            return value_processor(value)
        else:
            return value

    @staticmethod
    def process_narozeni(value: str) -> str:
        value = value.replace(" ", "").replace(",", ".")
        input_date = datetime.strptime(value, "%d.%m.%Y")
        return input_date.strftime("%Y-%m-%d")

    @staticmethod
    def process_psc(value: str) -> int:
        return int(value.replace(" ", ""))

    @staticmethod
    def process_pojistovna(value1: str, value2: str) -> str | None:
        value1 = InputFieldsCleaner._process_health_insurance_company_parser(value1)
        value2 = InputFieldsCleaner._process_health_insurance_company_parser(value2)

        if not value1 and not value2:
            return None
        if not value1:
            return InputFieldsCleaner._process_health_insurance_company_parser(value2)
        elif not value2 or value1 == value2:
            return InputFieldsCleaner._process_health_insurance_company_parser(value1)
        else:
            raise ValidationError(
                {
                    "health_insurance_company": f"Two different health insurance companies: {value1} and {value2}"
                }
            )

    @staticmethod
    def _process_health_insurance_company_parser(value):
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

    @staticmethod
    def process_sex_by_birth_number(birth_number):
        if not birth_number or len(birth_number.replace("/", "")) != 10:
            return None

        return Person.Sex.F if int(birth_number[2]) - 5 >= 0 else Person.Sex.M

    @staticmethod
    def process_type_by_date_of_birth(date_of_birth):
        if not date_of_birth:
            return Person.Type.UNKNOWN

        date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d")
        age = (
            today().year
            - date_of_birth.year
            - ((today().month, today().day) < (date_of_birth.month, date_of_birth.day))
        )

        return Person.Type.UNKNOWN if age >= 18 else Person.Type.CHILD


class OutputPrinter:
    def __init__(self, stdout, style):
        super().__init__()
        self.persons = []
        self.stdout = stdout
        self.style = style

    person_json_format = """{{
    "model": "persons.person",
    "pk": {id},
    "fields": {{
{fields}
    }}
}}"""

    user_json_format = """{{
    "model": "users.user",
    "pk": {id},
    "fields": {{
        "password": "{password}",
        "last_login": null,
        "is_superuser": false,
        "is_staff": false,
        "is_active": true,
        "groups": [],
        "user_permissions": []
    }}
}}"""

    def print_output(self, persons):
        self.stdout.write("[")

        persons_in_json = []
        for idx, person in enumerate(persons):
            persons_in_json.append(self._print_person_output(idx, person))

            if person.password:
                persons_in_json.append(self._print_user(idx, person.password))

        self.stdout.write(",\n".join(persons_in_json))

        self.stdout.write("]")

    def _print_person_output(self, idx, person):
        fields = person.__dict__

        fields_output = []
        for key, val in fields.items():
            if key.startswith("_") or key in ["id", "password"]:
                continue
            if not val:
                continue

            if key == "managing_persons":
                fields_output.append(f'\t\t"managed_persons": {val}')
            else:
                fields_output.append(f'\t\t"{key}": "{val}"')

        data = {"id": idx, "fields": ",\n".join(fields_output)}

        return self.person_json_format.format(**data)

    def _print_user(self, idx, password):
        data = {"id": idx, "password": password}

        return self.user_json_format.format(**data)
