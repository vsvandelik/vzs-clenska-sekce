from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Person(models.Model):
    class Type(models.TextChoices):
        CHILD = "dite", _("člen dítě")
        ADULT = "dospely", _("člen dospělý")
        EXPECTANT = "cekatel", _("člen čekatel")
        HONORARY = "cestny", _("čestný člen")
        EXTERNAL = "externi", _("externí spolupracovník")
        PARENT = "rodic", _("rodič")

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    person_type = models.CharField(max_length=10, choices=Type.choices)
    features = models.ManyToManyField("persons.Feature", through="FeatureAssignment")
    managed_people = models.ManyToManyField("self", symmetrical=False)

    def get_absolute_url(self):
        return reverse("persons:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Feature(models.Model):
    class Type(models.TextChoices):
        QUALIFICATION = "K", _("kvalifikace")
        POSSESSION = "V", _("vlastnictví")
        PERMIT = "O", _("oprávnění")

    feature_type = models.CharField(max_length=1, choices=Type.choices)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    name = models.CharField(max_length=50, unique=True)
    never_expires = models.BooleanField(default=False)
    tier = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class FeatureAssignment(models.Model):
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    feature = models.ForeignKey("persons.Feature", on_delete=models.CASCADE)
    date_assigned = models.DateField()
    date_expire = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["person", "feature"]


class Transaction(models.Model):
    amount = models.IntegerField()
    reason = models.CharField(max_length=150)
    date = models.DateField()
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.SET_NULL, null=True)
