from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import User
from . import forms


class CustomCreateMixin(generic.edit.CreateView):
    """
    Allows having multiple additional GET forms in one CreateView
    The purpose is for the GET forms to fill some hidden fields
    of the main POST form of the CreateView
    """

    get_form_classes = []

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

        for form_class in self.get_form_classes:
            form_name = form_class.name

            if form_id == form_name:
                form = form_class(self.request.GET)
            else:
                form = form_class(initial=self.get_initial(form_class))

            kwargs[form_name] = form

        for form_class in self.get_form_classes:
            form_name = form_class.name
            kwargs[form_name].handle(self.request, kwargs)

        return super().get_context_data(**kwargs)


class UserCreateView(CustomCreateMixin):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("users:add")
    get_form_classes = [forms.PersonSearchForm, forms.PersonSelectForm]


class IndexView(generic.list.ListView):
    context_object_name = "users"
    paginate_by = 2

    def get_queryset(self):
        self.user_search_form = forms.UserSearchForm(self.request.GET)
        self.user_search_pagination_form = forms.UserSearchPaginationForm(
            self.request.GET
        )
        return self.user_search_form.search_users()

    def get_context_data(self, **kwargs):
        kwargs["user_search_form"] = self.user_search_form
        kwargs["user_search_pagination_form"] = self.user_search_pagination_form
        return super().get_context_data(**kwargs)


class UserEditView(generic.edit.UpdateView):
    model = User
    template_name = "users/edit.html"
    form_class = forms.UserEditForm
