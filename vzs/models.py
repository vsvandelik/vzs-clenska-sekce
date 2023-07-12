from django.template.loader import render_to_string
from django.db import models


class RenderableModelMixin:
    def render(self, style, **kwargs):
        meta = self._meta
        template_name = f"{meta.app_label}/{meta.model_name}_render_{style}.html"

        kwargs.setdefault(meta.model_name, self)

        return render_to_string(template_name, kwargs)


class DatabaseSettingsMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
