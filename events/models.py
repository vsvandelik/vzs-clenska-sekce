from django.db import models
from django.utils.translation import gettext_lazy as _
from .utils import weekday_2_day_shortcut
from django.utils import timezone
from persons.models import Person
from features.models import Feature
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q


class Event(models.Manager):
    name = models.CharField(_("Název"), max_length=50)
    description = models.TextField(_("Popis"))

    # conditions for participants
    capacity = models.PositiveSmallIntegerField(
        _("Maximální počet účastníků"), null=True
    )
    min_age_enabled = models.BooleanField(default=False)
    min_age = models.PositiveSmallIntegerField(
        _("Minimální věk účastníků"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    group_membership_required = models.BooleanField(default=False)
    group = models.ForeignKey("groups.Group", null=True, on_delete=models.SET_NULL)
    allowed_person_types = models.ManyToManyField("persons.PersonType")
    ##############################

    enrolled_participants = models.ManyToManyField(
        "persons.Person", through="events.ParticipantEnrollment"
    )


class OneTimeEvent(Event):
    class Category(models.TextChoices):
        COMMERCIAL = "komercni", _("komerční")
        COURSE = "kurz", _("kurz")

    default_participant_fee = models.PositiveIntegerField(_("Poplatek za účast"))
    category = models.CharField(
        _("Druh události"), max_length=10, choices=Category.choices
    )


class Training(Event):
    class Category(models.TextChoices):
        CLIMBING = "lezecký", _("lezecký")
        SWIMMING = "plavecky", _("plavecký")

    date_start = models.DateField(_("Začíná"), null=True)
    date_end = models.DateField(_("Končí"), null=True)

    main_coach = models.ForeignKey("persons.Person", on_delete=models.SET_NULL)
    category = models.CharField(
        _("Druh události"), max_length=10, choices=Category.choices
    )

    po = models.BooleanField()
    ut = models.BooleanField()
    st = models.BooleanField()
    ct = models.BooleanField()
    pa = models.BooleanField()
    so = models.BooleanField()
    ne = models.BooleanField()

    def can_be_replace_by(self, training):
        pass  # TODO

    def replaces_training_list(self):
        pass  # TODO


class TrainingReplaceability(models.Manager):
    training_1 = models.ForeignKey("events.Training", on_delete=models.SET_NULL)
    training_2 = models.ForeignKey("events.Training", on_delete=models.SET_NULL)

    symmetric = models.BooleanField(default=True)
    # if false -> training_1 can replace training_2 but not vice-versa
    # if true -> training_1 can replace training_2 and vice-versa

    class Meta:
        unique_together = ["training_1", "training_2"]


class EventOccurrence(models.Manager):
    class State(models.TextChoices):
        FUTURE = "neuzavrena", _("neuzavřena")
        FINISHED = "uzavrena", _("uzavřena")
        APPROVED = "schvalena", _("schválena")

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    positions = models.ManyToManyField(
        "positions.EventPosition", through="events.EventPositionAssignment"
    )
    attending_organizers = models.ManyToManyField("persons.Person")

    attending_participants = models.ManyToManyField(
        "persons.Person", through="events.EventOccurrenceParticipation"
    )

    datetime_start = models.DateTimeField(_("Začíná"), null=True)
    datetime_end = models.DateTimeField(_("Končí"), null=True)
    state = models.CharField(max_length=10, choices=State.choices)

    def missing_participants(self):
        pass  # TODO:

    def enrolled_organizers(self):
        pass  # TODO:


class OneTimeEventOccurrence(EventOccurrence):
    hours = models.PositiveSmallIntegerField(
        _("Počet hodin"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )


class TrainingOccurrence(EventOccurrence):
    pass


class Enrollment(models.Manager):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    datetime = models.DateTimeField()


class ParticipantEnrollment(Enrollment):
    class State(models.TextChoices):
        WAITING = "ceka", _("čeká")
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=State.choices)


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey("positions.EventPosition", on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(
        _("Počet"), default=1, validators=[MinValueValidator(1)]
    )

    organizers = models.ManyToManyField("persons.Person")

    class Meta:
        unique_together = ["event", "position"]


class Participation(models.Model):
    class Meta:
        abstract = True

    class State(models.TextChoices):
        PRESENT = "pritomen", _("přítomen")
        MISSING = "nepritomen", _("nepřítomen")

    state = models.CharField(max_length=10, choices=State.choices)


class EventOccurrenceParticipation(Participation):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    event_occurrence = models.ForeignKey(
        "events.EventOccurrence", on_delete=models.CASCADE
    )
    actual_participation_fee = models.PositiveIntegerField(_("Poplatek za účast"))

    class Meta(Participation.Meta):
        unique_together = ["person", "event"]


class EventOrganization(Participation):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    event_position = models.ForeignKey(
        "events.EventPositionAssignment", on_delete=models.CASCADE
    )

    class Meta(Participation.Meta):
        unique_together = ["person", "event_position"]


#
#
#
#
#
# class OneTimeEventsManager(models.Manager):
#     def get_queryset(self):
#         return (
#             super()
#             .get_queryset()
#             .filter(parent=None)
#             .exclude(
#                 pk__in=list(
#                     Event.objects.all().values_list("parent", flat=True).distinct()
#                 )
#             )
#         )
#
#
# class ParentTrainingsManager(models.Manager):
#     def get_queryset(self):
#         return (
#             super()
#             .get_queryset()
#             .filter(
#                 parent=None,
#                 pk__in=list(
#                     Event.objects.all().values_list("parent", flat=True).distinct()
#                 ),
#             )
#         )
#
#
# class ChildTrainingsManager(models.Manager):
#     def get_queryset(self):
#         return super().get_queryset().filter(~Q(parent=None))
#
#
# class Event(models.Model):
#     objects = models.Manager()
#     one_time_events = OneTimeEventsManager()
#     parent_trainings = ParentTrainingsManager()
#     child_trainings = ChildTrainingsManager()
#
#     class State(models.TextChoices):
#         FUTURE = "neuzavrena", _("neuzavřena")
#         FINISHED = "uzavrena", _("uzavřena")
#         APPROVED = "schvalena", _("schválena")
#
#     parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
#     name = models.CharField(_("Název"), max_length=50)
#     description = models.TextField(_("Popis"))
#     time_start = models.DateTimeField(_("Začíná"), null=True)
#     time_end = models.DateTimeField(_("Končí"), null=True)
#     capacity = models.PositiveSmallIntegerField(
#         _("Maximální počet účastníků"), null=True
#     )
#     min_age_enabled = models.BooleanField(default=False)
#     min_age = models.PositiveSmallIntegerField(
#         _("Minimální věk účastníků"),
#         null=True,
#         blank=True,
#         validators=[MinValueValidator(1), MaxValueValidator(99)],
#     )
#     group_membership_required = models.BooleanField(default=False)
#     group = models.ForeignKey("groups.Group", null=True, on_delete=models.SET_NULL)
#     allowed_person_types = models.ManyToManyField("persons.PersonType")
#     price_list = models.ForeignKey(
#         "price_lists.PriceList", on_delete=models.SET_NULL, null=True
#     )
#     state = models.CharField(max_length=10, choices=State.choices)
#     positions = models.ManyToManyField(
#         "positions.EventPosition", through="events.EventPositionAssignment"
#     )
#     participants = models.ManyToManyField(Person, through="events.EventParticipation")
#
#     def _is_top(self):
#         return self.parent is None
#
#     def _is_top_training(self):
#         children = Event.objects.filter(parent__exact=self)
#         return self._is_top() and len(children) > 0
#
#     def _is_child_training(self):
#         return self.parent is not None
#
#     def _is_one_time_event(self):
#         return not self._is_top_training() and not self._is_child_training()
#
#     def set_type(self):
#         self.is_child_training = self._is_child_training()
#         self.is_top_training = self._is_top_training()
#         self.is_one_time_event = self._is_one_time_event()
#
#     def get_weekdays_trainings_occur(self):
#         weekdays = set()
#         children = self.get_children_trainings_sorted()
#         for child in children:
#             weekdays.add(child.time_start.weekday())
#         out = list(weekdays)
#         out.sort()
#         return out
#
#     def extend_2_top_training(self):
#         self.weekdays = self.get_weekdays_trainings_occur()
#         self.children = self.get_children_trainings_sorted()
#         for weekday in self.weekdays:
#             day_shortcut = weekday_2_day_shortcut(weekday)
#             for child in self.children:
#                 if child.time_start.weekday() == weekday:
#                     setattr(
#                         self,
#                         f"from_{day_shortcut}",
#                         child.time_start,
#                     )
#                     setattr(self, f"to_{day_shortcut}", child.time_end)
#                     break
#
#     def does_training_take_place_on_date(self, date):
#         for child in self.children:
#             if (
#                 timezone.localtime(child.time_start).date()
#                 <= date
#                 <= timezone.localtime(child.time_end).date()
#             ):
#                 return True
#         return False
#
#     def get_children_trainings_sorted(self):
#         children = Event.objects.filter(parent__exact=self).order_by("time_start")
#         for child in children:
#             child.time_start = timezone.localtime(child.time_start)
#             child.time_end = timezone.localtime(child.time_end)
#         return children
#
#     def get_not_signed_persons(self):
#         return Person.objects.all().difference(self.participants.all())
#
#     def get_approved_participants(self):
#         return self.participants.filter(state__exact=Participation.State.APPROVED)
#
#     def get_substitute_participants(self):
#         return self.participants.filter(state__exact=Participation.State.SUBSTITUTE)
#
#     def __str__(self):
#         return self.name
#
#     def delete(self, using=None, keep_parents=False):
#         if self.price_list is not None:
#             self.price_list.delete()
#         return super().delete(using, keep_parents)
#
#
# class EventPositionAssignment(models.Model):
#     event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
#     position = models.ForeignKey("positions.EventPosition", on_delete=models.CASCADE)
#     count = models.PositiveSmallIntegerField(
#         _("Počet"), default=1, validators=[MinValueValidator(1)]
#     )
#     organizers = models.ManyToManyField(Person, through="events.EventOrganization")
#
#     class Meta:
#         unique_together = ["event", "position"]
#
#
# class Participation(models.Model):
#     class Meta:
#         abstract = True
#
#     class State(models.TextChoices):
#         WAITING = "ceka", _("čeká")
#         APPROVED = "schvalen", _("schválen")
#         SUBSTITUTE = "nahradnik", _("nahradník")
#         PRESENT = "pritomen", _("přítomen")
#
#     state = models.CharField(max_length=10, choices=State.choices)
#
#
# class EventParticipation(Participation):
#     person = models.ForeignKey(Person, on_delete=models.CASCADE)
#     event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
#
#     class Meta(Participation.Meta):
#         unique_together = ["person", "event"]
#
#
# class EventOrganization(Participation):
#     person = models.ForeignKey(Person, on_delete=models.CASCADE)
#     event_position = models.ForeignKey(
#         "events.EventPositionAssignment", on_delete=models.CASCADE
#     )
#
#     class Meta(Participation.Meta):
#         unique_together = ["person", "event_position"]
#
#
# class EventRequirement(models.Model):
#     event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
#     feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
#     count = models.PositiveSmallIntegerField()
#
#     class Meta:
#         unique_together = ["event", "feature"]
