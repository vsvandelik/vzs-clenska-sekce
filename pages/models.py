from django.db import models
from django.urls import reverse

from django.utils.translation import gettext_lazy as _
from tinymce import models as tinymce_models


class Page(models.Model):
    class Meta:
        permissions = [("stranky", _("Správce textových stránek"))]

    title = models.CharField(_("Titulek"), max_length=255)
    content = tinymce_models.HTMLField(_("Obsah"), blank=True, null=True)
    slug = models.SlugField(_("URL"), max_length=255, unique=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pages:detail", kwargs={"slug": self.slug})
