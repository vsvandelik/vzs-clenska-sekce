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


def _csv_make_getter(field_name):
    return lambda instance: getattr(instance, field_name)


class ExportableCSVMixin:
    csv_filter = lambda _: True
    csv_order = []
    csv_labels = {}
    csv_getters = {}
    __labels = None
    __getters = None

    @classmethod
    def __init(cls):
        fields = [
            field for field in cls._meta.get_fields() if field.name in cls.csv_order
        ]

        labels = {
            field.name: (
                field.verbose_name if hasattr(field, "verbose_name") else field.name
            )
            for field in fields
        }
        labels.update(cls.csv_labels)

        getters = {field.name: _csv_make_getter(field.name) for field in fields}
        getters.update(cls.csv_getters)

        cls.__labels = [labels[field_name] for field_name in cls.csv_order]
        cls.__getters = [getters[field_name] for field_name in cls.csv_order]

    @classmethod
    def csv_header(cls):
        if cls.__labels is None:
            cls.__init()

        return cls.__labels

    def csv_row(self):
        return [getter(self) for getter in self.__getters]
