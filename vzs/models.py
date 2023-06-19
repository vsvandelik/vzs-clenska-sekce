from django.template.loader import render_to_string


class RenderableModelMixin:
    def render(self, style, **kwargs):
        meta = self._meta
        template_name = f"{meta.app_label}/{meta.model_name}_render_{style}.html"

        if meta.model_name not in kwargs:
            kwargs[meta.model_name] = self

        return render_to_string(template_name, kwargs)
