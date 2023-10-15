import random
from datetime import timedelta, date

import unidecode
from django.core.management import BaseCommand
from django.db.models import Q

from features.models import Feature, FeatureAssignment
from groups.models import Group
from persons.models import Person
from positions.models import EventPosition
from transactions.models import Transaction, FioTransaction
from vzs.management.commands.data_list import names, addresses


class Command(BaseCommand):
    help = "Add real demo data to the database"

    def handle(self, *args, **options):
        self._add_qualifications()
        self._add_permissions()
        self._add_equipment()

        self._add_groups()

        self._add_positions()

        self._add_persons_children()
        self._add_persons_others()

        self.stdout.write(self.style.SUCCESS(f"Successfully added some demo data."))

    def _add_qualifications(self):
        Feature.objects.filter(feature_type=Feature.Type.QUALIFICATION).delete()

        internal_category = Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Interní kvalifikace VZS",
            assignable=False,
        )
        internal_licences = [
            (0, "Mladý záchranář 7"),
            (1, "Mladý záchranář 6"),
            (2, "Mladý záchranář 5"),
            (10, "Záchranářské minimum"),
            (10, "Minimum VZS pro volnou vodu"),
            (30, "Vůdce záchranného plavidla"),
            (20, "Záchranář 3"),
            (50, "Záchranář 2"),
            (50, "Záchranář VZS"),
            (100, "Školitel první pomoci"),
            (200, "Školitel pro bazénové kvalifikace"),
            (500, "Instruktor VZS"),
            (1000, "Lektor VZS"),
        ]
        for tier, licence in internal_licences:
            Feature.objects.create(
                feature_type=Feature.Type.QUALIFICATION,
                name=licence,
                assignable=True,
                never_expires=False,
                tier=tier,
                parent=internal_category,
            )

        nsk_category = Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Národní soustava kvalifikací",
            assignable=False,
        )
        nsk_licences = [
            "Plavčík/plavčice",
            "Mistr/mistrová plavčí",
            "Záchranář/záchranářka na volné vodě",
            "Instruktor/instruktorka vodní turistiky",
            "Instruktor/instruktorka plavání",
        ]
        for licence in nsk_licences:
            Feature.objects.create(
                feature_type=Feature.Type.QUALIFICATION,
                name=licence,
                assignable=True,
                collect_codes=True,
                never_expires=True,
                parent=nsk_category,
            )

        driving_licence_category = Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Řidičské oprávnění",
            assignable=False,
        )
        driving_licences = ["B", "B+E", "B96", "C"]
        for licence in driving_licences:
            Feature.objects.create(
                feature_type=Feature.Type.QUALIFICATION,
                name=licence,
                assignable=True,
                collect_codes=True,
                never_expires=True,
                parent=driving_licence_category,
            )

        boat_category = Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Vůdce malého plavidla",
            assignable=False,
        )
        boat_licences = ["M", "M20", "S", "S20", "C"]
        for licence in boat_licences:
            Feature.objects.create(
                feature_type=Feature.Type.QUALIFICATION,
                name=licence,
                assignable=True,
                collect_codes=True,
                never_expires=True,
                parent=boat_category,
            )

        medical_category = Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Zdravotnické kvalifikace",
            assignable=False,
        )
        medical_licences = [
            "Lékař",
            "Zdravotnický záchranář",
            "Zdravotník zotavovacích akcí",
        ]
        for licence in medical_licences:
            Feature.objects.create(
                feature_type=Feature.Type.QUALIFICATION,
                name=licence,
                assignable=True,
                collect_codes=True,
                never_expires=True,
                collect_issuers=True,
                parent=medical_category,
            )

        Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Trenér plavání",
            assignable=True,
            collect_codes=True,
            collect_issuers=True,
            never_expires=True,
        )
        Feature.objects.create(
            feature_type=Feature.Type.QUALIFICATION,
            name="Instruktor lezení",
            assignable=True,
            collect_codes=True,
            collect_issuers=True,
            never_expires=True,
        )

    def _add_permissions(self):
        Feature.objects.filter(feature_type=Feature.Type.PERMISSION).delete()

        permissions_list = {
            "Řídit auta": [
                "Nissan",
                "Nová sanitka",
                "Transit nový",
                "Transit starý",
                "Amarok",
            ],
            "Řídit čluny": [
                "Czech marine - 5Hp",
                "Hifi - Suzuki 15Hp",
                "Bombard - Mercury 9.9Hp",
                "Aka marine - 20Hp",
                "Brig - Tohatsu 50Hp",
                "Sportis 40Hp",
                "Pioner 70HP",
                "Plecháč 150Hp",
                "Sportis 7500 - Honda 2x 150Hp",
                "Plachetnice",
            ],
            "Ostatní": ["Vedení výjezdu", "Vození dětí"],
        }

        for permission_category_name, permission_licences in permissions_list.items():
            category = Feature.objects.create(
                feature_type=Feature.Type.PERMISSION,
                name=permission_category_name,
                assignable=False,
            )
            for permission in permission_licences:
                Feature.objects.create(
                    feature_type=Feature.Type.PERMISSION,
                    name=permission,
                    assignable=True,
                    never_expires=True,
                    parent=category,
                )

    def _add_equipment(self):
        Feature.objects.filter(feature_type=Feature.Type.EQUIPMENT).delete()

        unlimited_equipment = {"Komplet", "Vesta", "Helma", "Nůž", "Klíče od Lahovic"}

        for equipment in unlimited_equipment:
            Feature.objects.create(
                feature_type=Feature.Type.EQUIPMENT,
                name=equipment,
                assignable=True,
                never_expires=True,
            )

        Feature.objects.create(
            feature_type=Feature.Type.EQUIPMENT,
            name="Ploutve",
            assignable=True,
            never_expires=False,
            fee=200,
            collect_codes=True,
        )

    def _add_groups(self):
        Group.objects.all().delete()

        Group.objects.create(name="Dospělí", google_as_members_authority=False)
        Group.objects.create(name="Trenéři plavání", google_as_members_authority=False)
        Group.objects.create(name="Trenéři lezení", google_as_members_authority=False)
        Group.objects.create(name="Tým IZS", google_as_members_authority=False)
        Group.objects.create(name="Velitelé - Orlík", google_as_members_authority=False)
        Group.objects.create(name="Představenstvo", google_as_members_authority=False)

    def _add_positions(self):
        EventPosition.objects.all().delete()

        EventPosition.objects.create(
            name="Zdravotník", min_age=18, wage_hour=50
        ).required_features.add(
            Feature.objects.get(name="Zdravotník zotavovacích akcí")
        )

        EventPosition.objects.create(name="Velitel", min_age=18, wage_hour=30)

        ridic_clunu = EventPosition.objects.create(
            name="Řidič člunu", min_age=18, wage_hour=0
        )
        ridic_clunu.required_features.add(
            Feature.objects.get(name="Vůdce záchranného plavidla")
        )
        ridic_clunu.required_features.add(Feature.objects.get(name="Záchranář VZS"))

        EventPosition.objects.create(
            name="Řidič auta (bez B+E)", min_age=18, wage_hour=0
        ).required_features.add(Feature.objects.get(name="B"))

        EventPosition.objects.create(
            name="Řidič auta s velkým vozíkem", min_age=18, wage_hour=0
        ).required_features.add(Feature.objects.get(name="B+E"))

        trener_plavani = EventPosition.objects.create(
            name="Trenér plavání",
            min_age=18,
            wage_hour=0,
            group=Group.objects.get(name="Trenéři plavání"),
        )
        trener_plavani.required_features.add(Feature.objects.get(name="Trenér plavání"))
        trener_plavani.required_features.add(
            Feature.objects.get(name="Plavčík/plavčice")
        )

        EventPosition.objects.create(
            name="Instruktor lezení",
            min_age=18,
            wage_hour=0,
            group=Group.objects.get(name="Trenéři lezení"),
        ).required_features.add(Feature.objects.get(name="Instruktor lezení"))

    def _add_persons_children(self):
        Person.objects.filter(
            Q(person_type=Person.Type.CHILD) | Q(person_type=Person.Type.PARENT)
        ).delete()

        # Setting age boundaries for children
        max_birthdate = date.today() - timedelta(days=(6 * 365))
        min_birthdate = date.today() - timedelta(days=(17 * 365))

        for name in names[:100]:
            first_name, last_name = name.split(" ")
            new_person = Person(
                email=f"{unidecode.unidecode(first_name)}.{unidecode.unidecode(last_name)}@email.cz",
                first_name=first_name,
                last_name=last_name,
                date_of_birth=min_birthdate
                + timedelta(
                    days=random.randint(0, (max_birthdate - min_birthdate).days)
                ),
                sex=random.choices(Person.Sex.values)[0],
                person_type="dite",
                birth_number=f"{random.randint(0, 99):02}{random.randint(0, 12):02}{random.randint(0, 31):02}",
                health_insurance_company=random.choices(
                    Person.HealthInsuranceCompany.values
                )[0],
            )

            if random.randint(0, 2) == 1:
                new_person.phone = f"{random.randint(600000000, 799999999)}"

            if random.randint(0, 2) == 1:
                new_person.street, new_person.city, postcode = random.choice(addresses)
                new_person.postcode = int(postcode.replace(" ", ""))

            if random.randint(0, 2) == 1:
                new_person.swimming_time = f"{random.randint(0, 1):02}:{random.randint(0, 59):02}.{random.randint(0, 99):02}"

            new_person.save()

            if random.randint(0, 4) == 1:
                assigned_feature = FeatureAssignment.objects.create(
                    feature=Feature.objects.get(name="Ploutve"),
                    person=new_person,
                    date_assigned=date(date.today().year, 9, random.randint(1, 30)),
                    date_expire=date(date.today().year + 1, 6, random.randint(1, 30)),
                    code=f"Ploutve č. {random.randint(0, 999):03}",
                )

                fio_transaction = None
                if random.randint(0, 1) == 1:
                    fio_transaction = FioTransaction.objects.create(
                        date_settled=date.today(),
                        fio_id=random.randint(0, 999999999),
                    )

                Transaction.objects.create(
                    person=new_person,
                    amount=-Feature.objects.get(name="Ploutve").fee,
                    feature_assigment=assigned_feature,
                    reason="Poplatek za ploutve",
                    date_due=assigned_feature.date_assigned + timedelta(days=30),
                    fio_transaction=fio_transaction,
                )

            for i in range(random.randint(0, 4)):
                existing_parents = Person.objects.filter(person_type="rodic").all()

                if random.randint(0, 4) == 1:  # existing parent
                    new_person.managed_by.add(random.choice(existing_parents))
                else:
                    new_parent = Person.objects.create(
                        first_name=f"Rodič {i}",
                        last_name=last_name,
                        email=f"rodic.{i}.{unidecode.unidecode(first_name)}.{unidecode.unidecode(last_name)}@email.cz",
                        person_type="rodic",
                    )

                    new_person.managed_by.add(new_parent)

    def _add_persons_others(self):
        Person.objects.exclude(
            Q(person_type=Person.Type.CHILD) | Q(person_type=Person.Type.PARENT)
        ).delete()

        # Setting age boundaries for children
        max_birthdate = date.today() - timedelta(days=(18 * 365))
        min_birthdate = date.today() - timedelta(days=(100 * 365))

        for name in names[100:]:
            first_name, last_name = name.split(" ")
            new_person = Person(
                email=f"{unidecode.unidecode(first_name)}.{unidecode.unidecode(last_name)}@email.cz",
                first_name=first_name,
                last_name=last_name,
                date_of_birth=min_birthdate
                + timedelta(
                    days=random.randint(0, (max_birthdate - min_birthdate).days)
                ),
                phone=f"{random.randint(600000000, 799999999)}",
                sex=random.choices(Person.Sex.values)[0],
                person_type=random.choice(
                    [
                        Person.Type.ADULT,
                        Person.Type.EXTERNAL,
                        Person.Type.HONORARY,
                        Person.Type.FORMER,
                    ]
                ),
                birth_number=f"{random.randint(0, 99):02}{random.randint(0, 12):02}{random.randint(0, 31):02}",
                health_insurance_company=random.choices(
                    Person.HealthInsuranceCompany.values
                )[0],
            )

            new_person.street, new_person.city, postcode = random.choice(addresses)
            new_person.postcode = int(postcode.replace(" ", ""))

            new_person.save()

            all_qualifications = Feature.qualifications.all()
            all_permissions = Feature.permissions.all()
            all_equipments = Feature.equipments.all()

            for i in range(random.randint(0, 8)):
                FeatureAssignment.objects.create(
                    feature=random.choice(all_qualifications),
                    person=new_person,
                    date_assigned=new_person.date_of_birth
                    + timedelta(
                        days=random.randint(
                            0, (date.today() - new_person.date_of_birth).days
                        )
                    ),
                )

            for i in range(random.randint(0, 8)):
                FeatureAssignment.objects.create(
                    feature=random.choice(all_permissions),
                    person=new_person,
                    date_assigned=new_person.date_of_birth
                    + timedelta(
                        days=random.randint(
                            0, (date.today() - new_person.date_of_birth).days
                        )
                    ),
                )

            for i in range(random.randint(0, 8)):
                FeatureAssignment.objects.create(
                    feature=random.choice(all_equipments),
                    person=new_person,
                    date_assigned=new_person.date_of_birth
                    + timedelta(
                        days=random.randint(
                            0, (date.today() - new_person.date_of_birth).days
                        )
                    ),
                )

            new_person.groups.add(Group.objects.get(name="Dospělí"))

            if random.randint(0, 5) == 1:
                new_person.groups.add(Group.objects.get(name="Tým IZS"))

            if random.randint(0, 5) == 1:
                new_person.groups.add(Group.objects.get(name="Velitelé - Orlík"))

            if random.randint(0, 5) == 1:
                new_person.groups.add(Group.objects.get(name="Představenstvo"))

            if new_person.featureassignment_set.contains(
                Feature.objects.get(name="Trenér plavání")
            ):
                new_person.groups.add(Group.objects.get(name="Trenéři plavání"))

            if new_person.featureassignment_set.contains(
                Feature.objects.get(name="Instruktor lezení")
            ):
                new_person.groups.add(Group.objects.get(name="Trenéři lezení"))
