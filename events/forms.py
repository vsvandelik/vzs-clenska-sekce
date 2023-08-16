from django.forms import ModelForm, MultipleChoiceField
from django_select2.forms import Select2Widget

from positions.models import EventPosition
from .forms_bases import AgeLimitForm, GroupMembershipForm, AllowedPersonTypeForm
from .models import Event, EventPositionAssignment


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class EventPositionAssignmentForm(ModelForm):
    class Meta:
        model = EventPositionAssignment
        fields = [
            "position",
            "count",
        ]
        labels = {"position": "Pozice"}
        widgets = {
            "position": Select2Widget(attrs={"onchange": "positionChanged(this)"})
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.position = kwargs.pop("position", None)
        super().__init__(*args, **kwargs)
        self.fields["count"].widget.attrs["min"] = 1
        if self.position is not None:
            self.fields["position"].widget.attrs["disabled"] = True
        else:
            self.fields["position"].queryset = EventPosition.objects.filter(
                pk__in=EventPosition.objects.all()
                .values_list("pk", flat=True)
                .difference(
                    EventPositionAssignment.objects.filter(
                        event=self.event
                    ).values_list("position_id", flat=True)
                )
            )

    def save(self, commit=True):
        instance = super().save(False)
        if self.instance.id is None:
            instance.event = self.event
        else:
            instance.position = self.position
        if commit:
            instance.save()
        return instance


class EventAgeLimitForm(AgeLimitForm):
    class Meta:
        model = Event
        fields = ["min_age", "max_age"]


class EventGroupMembershipForm(GroupMembershipForm):
    class Meta:
        model = Event
        fields = ["group"]
        labels = {"group": "Skupina"}
        widgets = {
            "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
        }


class EventAllowedPersonTypeForm(AllowedPersonTypeForm):
    class Meta:
        model = EventPosition
        fields = []
