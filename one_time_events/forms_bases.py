from django.forms import CheckboxSelectMultiple, ModelForm

from events.forms import MultipleChoiceFieldNoValidation
from events.forms_bases import OrganizerEnrollMyselfForm
from one_time_events.models import OrganizerOccurrenceAssignment


class OneTimeEventOrganizerEnrollMyselfForm(OrganizerEnrollMyselfForm):
    occurrences = MultipleChoiceFieldNoValidation(widget=CheckboxSelectMultiple)

    class Meta(OrganizerEnrollMyselfForm.Meta):
        model = OrganizerOccurrenceAssignment
