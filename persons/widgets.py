from django_select2.forms import ModelSelect2Widget


class PersonSelectWidget(ModelSelect2Widget):
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
    ]

    def label_from_instance(self, person):
        if person.date_of_birth is None:
            return f"{person.first_name} {person.last_name}"
        else:
            return (
                f"{person.first_name} {person.last_name} ({person.date_of_birth.year})"
            )
