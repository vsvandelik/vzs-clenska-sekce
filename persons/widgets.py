from django_select2.forms import ModelSelect2Widget


class PersonSelectWidget(ModelSelect2Widget):
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
    ]
