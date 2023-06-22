from django.db import models
from django.utils.translation import gettext_lazy as _
from .utils import weekday_2_day_shortcut
from django.utils import timezone


class Event(models.Model):
    class State(models.TextChoices):
        FUTURE = "neuzavrena", _("neuzavřena")
        FINISHED = "uzavrena", _("uzavřena")
        APPROVED = "schvalena", _("schválena")

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)
    description = models.TextField()
    time_start = models.DateTimeField(null=True)
    time_end = models.DateTimeField(null=True)
    capacity = models.PositiveSmallIntegerField(null=True)
    age_limit = models.PositiveSmallIntegerField(null=True)
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

    def is_top(self):
        return self.parent == None

    def is_top_training(self):
        children = Event.objects.filter(parent__exact=self)
        return self.is_top() and len(children) > 0

    def get_weekdays_trainings_occur(self):
        weekdays = set()
        children = Event.objects.filter(parent__exact=self)
        for child in children:
            weekdays.add(timezone.localtime(child.time_start).weekday())
        out = list(weekdays)
        out.sort()
        return out

    def extend_2_top_training(self):
        self.weekdays = self.get_weekdays_trainings_occur()
        self.children = self.get_children_trainings_sorted()
        for weekday in self.weekdays:
            day_shortcut = weekday_2_day_shortcut(weekday)
            for child in self.children:
                child_time_start_local = timezone.localtime(child.time_start)
                if child_time_start_local.weekday() == weekday:
                    setattr(
                        self,
                        f"from_{day_shortcut}",
                        child_time_start_local,
                    )
                    setattr(
                        self, f"to_{day_shortcut}", timezone.localtime(child.time_end)
                    )
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
        return Event.objects.filter(parent__exact=self).order_by("time_start")

    def __str__(self):
        return f"{self.name}"


class EventPosition(models.Model):
    name = models.CharField(max_length=50)
    required_features = models.ManyToManyField("persons.Feature")


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey("events.EventPosition", on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(default=1)
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
