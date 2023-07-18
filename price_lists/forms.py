from django.forms import ModelForm
from .models import PriceListBonus
from features.models import Feature
from django_select2.forms import Select2Widget


class AddEditBonusForm(ModelForm):
    class Meta:
        fields = ["feature", "extra_payment"]
        model = PriceListBonus
        labels = {"feature": "Kvalifikace"}
        widgets = {
            "feature": Select2Widget(attrs={"onchange": "qualificationChanged(this)"})
        }

    def __init__(self, *args, **kwargs):
        self.price_list = kwargs.pop("price_list")
        super().__init__(*args, **kwargs)
        self.fields["extra_payment"].widget.attrs["min"] = 1
        self.fields["feature"].queryset = Feature.qualifications.exclude(
            pk__in=self.price_list.bonus_features.all()
        )
        if self.instance.id is not None:
            self.fields["feature"].queryset = self.fields[
                "feature"
            ].queryset | Feature.qualifications.filter(pk=self.instance.feature.pk)

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        instance = self.instance
        instance.price_list = self.price_list
        instance.feature = cleaned_data["feature"]
        instance.extra_payment = cleaned_data["extra_payment"]
        if commit:
            instance.save()
        return instance
