from django.views.generic import base as views
from django.views.generic import edit as views
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from . import forms


class CustomCreateMixin(views.CreateView):
    def get_initial(self, form_class=None):
        if form_class == None:
            form_class = self.form_class

        return {
            declared_field: self.request.GET.get(declared_field)
            for declared_field in form_class.declared_fields
            if declared_field != "form_id"
        }

    def success_message(self):
        return _(f"{str(self.object)} úspěšně přidán.")

    def form_valid(self, form):
        result = super().form_valid(form)

        messages.success(self.request, self.success_message())

        return result

    def get_context_data(self, **kwargs):
        form_id = self.request.GET.get("form_id")

        for get_form_class in self.get_form_classes:
            form_meta = get_form_class.Meta
            form_name = form_meta.name

            if form_id == form_name or form_meta.always_bound:
                form = get_form_class(self.request.GET)
            else:
                form = get_form_class(initial=self.get_initial(get_form_class))

            kwargs[form_name] = form

        for get_form_class in self.get_form_classes:
            form_name = get_form_class.Meta.name
            kwargs[form_name].handle(self.request, kwargs)

        return super().get_context_data(**kwargs)


class UserCreateView(CustomCreateMixin):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("users:add")
    get_form_classes = [forms.PersonSearchForm, forms.PersonSelectForm]
