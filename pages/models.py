from django.db.models import CharField, DateTimeField, Model, SlugField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField


class Page(Model):
    class Meta:
        permissions = [("stranky", _("Správce textových stránek"))]

    title = CharField(_("Titulek"), max_length=255)
    content = HTMLField(_("Obsah"), blank=True, null=True)
    slug = SlugField(_("URL"), max_length=255, unique=True)
    last_update = DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pages:detail", kwargs={"slug": self.slug})
