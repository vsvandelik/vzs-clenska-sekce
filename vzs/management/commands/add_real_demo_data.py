from django.core.management import BaseCommand

from features.models import Feature
from groups.models import Group
from positions.models import EventPosition
from price_lists.models import PriceList, PriceListBonus


class Command(BaseCommand):
    help = "Add real demo data to the database"

    def handle(self, *args, **options):
        # self._add_qualifications()
        # self._add_permissions()
        # self._add_equipment()

        # self._add_groups()

        # self._add_positions()

        self._add_price_lists()

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
            name="Zdravotník", min_age=18, min_age_enabled=True
        ).required_features.add(
            Feature.objects.get(name="Zdravotník zotavovacích akcí")
        )

        EventPosition.objects.create(name="Velitel", min_age=18, min_age_enabled=True)

        ridic_clunu = EventPosition.objects.create(
            name="Řidič člunu", min_age=18, min_age_enabled=True
        )
        ridic_clunu.required_features.add(
            Feature.objects.get(name="Vůdce záchranného plavidla")
        )
        ridic_clunu.required_features.add(Feature.objects.get(name="Záchranář VZS"))

        EventPosition.objects.create(
            name="Řidič auta (bez B+E)", min_age=18, min_age_enabled=True
        ).required_features.add(Feature.objects.get(name="B"))

        EventPosition.objects.create(
            name="Řidič auta s velkým vozíkem", min_age=18, min_age_enabled=True
        ).required_features.add(Feature.objects.get(name="B+E"))

        trener_plavani = EventPosition.objects.create(
            name="Trenér plavání",
            min_age=18,
            min_age_enabled=True,
            group_membership_required=True,
            group=Group.objects.get(name="Trenéři plavání"),
        )
        trener_plavani.required_features.add(Feature.objects.get(name="Trenér plavání"))
        trener_plavani.required_features.add(
            Feature.objects.get(name="Plavčík/plavčice")
        )

        EventPosition.objects.create(
            name="Instruktor lezení",
            min_age=18,
            min_age_enabled=True,
            group_membership_required=True,
            group=Group.objects.get(name="Trenéři lezení"),
        ).required_features.add(Feature.objects.get(name="Instruktor lezení"))

    def _add_price_lists(self):
        PriceList.objects.all().delete()

        zajistovacka_celodenni = PriceList.objects.create(
            name="Komerční zajišťovací akce",
            salary_base=2000,
            participant_fee=0,
            is_template=True,
        )
        PriceListBonus.objects.create(
            price_list=zajistovacka_celodenni,
            feature=Feature.objects.get(name="Vůdce záchranného plavidla"),
            extra_salary=300,
        )
        PriceListBonus.objects.create(
            price_list=zajistovacka_celodenni,
            feature=Feature.objects.get(name="Záchranář VZS"),
            extra_salary=500,
        )

        zajistovacka_puldenni = PriceList.objects.create(
            name="Komerční zajišťovací akce - půlden",
            salary_base=1000,
            participant_fee=0,
            is_template=True,
        )
        PriceListBonus.objects.create(
            price_list=zajistovacka_puldenni,
            feature=Feature.objects.get(name="Vůdce záchranného plavidla"),
            extra_salary=150,
        )
        PriceListBonus.objects.create(
            price_list=zajistovacka_puldenni,
            feature=Feature.objects.get(name="Záchranář VZS"),
            extra_salary=250,
        )

        prezentacni_akce = PriceList.objects.create(
            name="Prezentační akce",
            salary_base=2000,
            participant_fee=0,
            is_template=True,
        )

        trenink = PriceList.objects.create(
            name="Trénink", salary_base=200, participant_fee=0, is_template=True
        )
        PriceListBonus.objects.create(
            price_list=trenink,
            feature=Feature.objects.get(name="Trenér plavání"),
            extra_salary=20,
        )
        PriceListBonus.objects.create(
            price_list=trenink,
            feature=Feature.objects.get(name="Plavčík/plavčice"),
            extra_salary=20,
        )

        kurz_plavcik = PriceList.objects.create(
            name="Kurz plavčík 2023",
            salary_base=2000,
            participant_fee=3000,
            is_template=False,
        )
