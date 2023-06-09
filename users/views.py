from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from django.views.generic.base import TemplateResponseMixin
from django.contrib import messages

from persons.models import Person

from .forms import PersonSearchForm, UserCreateForm
from .models import User


class UserCreateView(TemplateResponseMixin, View):
    template_name = "users/create.html"

    def get(self, request, *args, **kwargs):
        search_form = PersonSearchForm(request.GET)
        create_form = UserCreateForm(
            initial={key: request.GET.get(key, "") for key in request.GET}
        )

        people = search_form.search_people()

        return self.render_to_response(
            {
                "create_form": create_form,
                "search_form": search_form,
                "people": people,
            }
        )

    def post(self, request, *args, **kwargs):
        search_form = PersonSearchForm(request.POST)
        create_form = UserCreateForm(request.POST)

        people = search_form.search_people()

        if create_form.is_valid():
            new_user = create_form.save()
            person = new_user.person
            messages.success(
                request,
                f"User for Person {person.first_name} {person.last_name} added.",
            )

        return self.render_to_response(
            {
                "create_form": create_form,
                "search_form": search_form,
                "people": people,
            }
        )
