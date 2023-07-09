from django.db import models
from django.urls import reverse

from django.utils.translation import gettext_lazy as _


class Page(models.Model):
    title = models.CharField(_("Titulek"), max_length=255)
    content = models.TextField(_("Obsah"))
    slug = models.SlugField(_("URL"), max_length=255, unique=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pages:detail", kwargs={"slug": self.slug})
