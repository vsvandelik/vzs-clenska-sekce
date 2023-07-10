from django.db import models
from django.utils.translation import gettext_lazy as _
from .utils import weekday_2_day_shortcut
from django.utils import timezone
from persons.models import Person, Feature
from django.core.validators import MaxValueValidator, MinValueValidator


class Event(models.Model):
    class State(models.TextChoices):
        FUTURE = "neuzavrena", _("neuzavřena")
        FINISHED = "uzavrena", _("uzavřena")
        APPROVED = "schvalena", _("schválena")

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    name = models.CharField(_("Název"), max_length=50)
    description = models.TextField(_("Popis"))
    time_start = models.DateTimeField(_("Začíná"), null=True)
    time_end = models.DateTimeField(_("Končí"), null=True)
    capacity = models.PositiveSmallIntegerField(
        _("Maximální počet účastníků"), null=True
    )
    age_limit = models.PositiveSmallIntegerField(
        _("Minimální věk účastníků"), null=True
    )
    price_list = models.ForeignKey(
        "events.PriceList", on_delete=models.SET_NULL, null=True
    )
    state = models.CharField(max_length=10, choices=State.choices)
    positions = models.ManyToManyField(
        "events.EventPosition", through="events.EventPositionAssignment"
    )
    participants = models.ManyToManyField(
        "persons.Person", through="events.EventParticipation"
    )
    requirements = models.ManyToManyField(
        "persons.Feature", through="events.EventRequirement"
    )

    def _is_top(self):
        return self.parent == None

    def _is_top_training(self):
        children = Event.objects.filter(parent__exact=self)
        return self._is_top() and len(children) > 0

    def _is_child_training(self):
        return self.parent is not None

    def _is_one_time_event(self):
        return not self._is_top_training() and not self._is_child_training()

    def set_type(self):
        self.is_child_training = self._is_child_training()
        self.is_top_training = self._is_top_training()
        self.is_one_time_event = self._is_one_time_event()

    def get_weekdays_trainings_occur(self):
        weekdays = set()
        children = self.get_children_trainings_sorted()
        for child in children:
            weekdays.add(child.time_start.weekday())
        out = list(weekdays)
        out.sort()
        return out

    def extend_2_top_training(self):
        self.weekdays = self.get_weekdays_trainings_occur()
        self.children = self.get_children_trainings_sorted()
        for weekday in self.weekdays:
            day_shortcut = weekday_2_day_shortcut(weekday)
            for child in self.children:
                if child.time_start.weekday() == weekday:
                    setattr(
                        self,
                        f"from_{day_shortcut}",
                        child.time_start,
                    )
                    setattr(self, f"to_{day_shortcut}", child.time_end)
                    break

    def does_training_take_place_on_date(self, date):
        for child in self.children:
            if (
                timezone.localtime(child.time_start).date()
                <= date
                <= timezone.localtime(child.time_end).date()
            ):
                return True
        return False

    def get_children_trainings_sorted(self):
        children = Event.objects.filter(parent__exact=self).order_by("time_start")
        for child in children:
            child.time_start = timezone.localtime(child.time_start)
            child.time_end = timezone.localtime(child.time_end)
        return children

    def get_not_signed_persons(self):
        return Person.objects.all().difference(self.participants.all())

    def get_approved_participants(self):
        return self.participants.filter(state__exact=Participation.State.APPROVED)

    def get_substitute_participants(self):
        return self.participants.filter(state__exact=Participation.State.SUBSTITUTE)

    def __str__(self):
        return self.name


class EventPosition(models.Model):
    name = models.CharField(_("Jméno"), max_length=50)
    required_features = models.ManyToManyField("persons.Feature")

    def required_qualifications(self):
        return self.required_features.filter(feature_type=Feature.Type.QUALIFICATION)

    def required_permissions(self):
        return self.required_features.filter(feature_type=Feature.Type.PERMISSION)

    def required_equipment(self):
        return self.required_features.filter(feature_type=Feature.Type.EQUIPMENT)

    def __str__(self):
        return self.name


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey("events.EventPosition", on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(
        _("Počet"), default=1, validators=[MinValueValidator(1)]
    )
    organizers = models.ManyToManyField(
        "persons.Person", through="events.EventOrganization"
    )

    class Meta:
        unique_together = ["event", "position"]


class Participation(models.Model):
    class Meta:
        abstract = True

    class State(models.TextChoices):
        WAITING = "ceka", _("čeká")
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")
        PRESENT = "pritomen", _("přítomen")

    state = models.CharField(max_length=10, choices=State.choices)


class EventParticipation(Participation):
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    class Meta(Participation.Meta):
        unique_together = ["person", "event"]


class EventOrganization(Participation):
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event_position = models.ForeignKey(
        "events.EventPositionAssignment", on_delete=models.CASCADE
    )

    class Meta(Participation.Meta):
        unique_together = ["person", "event_position"]


class EventRequirement(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    feature = models.ForeignKey("persons.Feature", on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ["event", "feature"]


class PriceList(models.Model):
    salary_base = models.PositiveIntegerField()
    bonuses = models.ManyToManyField("persons.Feature", through="events.PriceListBonus")


class PriceListBonus(models.Model):
    price_list = models.ForeignKey("events.PriceList", on_delete=models.CASCADE)
    feature = models.ForeignKey("persons.Feature", on_delete=models.CASCADE)
    bonus = models.PositiveIntegerField()

    class Meta:
        unique_together = ["price_list", "feature"]
