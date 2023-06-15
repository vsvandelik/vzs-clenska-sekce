from django.template.loader import get_template, render_to_string


class RenderableModelMixin:
    @property
    def render_inline(self):
        meta = self._meta
        template_name = f"{meta.app_label}/{meta.model_name}_render_inline.html"
        return render_to_string(template_name, context={"object": self})
