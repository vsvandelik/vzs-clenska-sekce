from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from django.views.generic.base import TemplateResponseMixin

from persons.models import Person

from .forms import PersonSearchForm, UserCreationForm
from .models import User


class CreateView(TemplateResponseMixin, View):
    template_name = 'users/create.html'

    def get(self, request, *args, **kwargs):
        search_form = PersonSearchForm(request.GET)
        creation_form = UserCreationForm()

        people = []

        if search_form.is_valid():
            query = search_form.cleaned_data['query']
            people = Person.objects.filter(name__contains=query)

        return self.render_to_response({'creation_form': creation_form, 'search_form': search_form, 'people': people, 'message': ''})

    def post(self, request, *args, **kwargs):
        search_form = PersonSearchForm()
        creation_form = UserCreationForm(request.POST)

        message = ''

        if creation_form.is_valid():
            new_user = creation_form.save()
            message = f'A User account for Person `{new_user.person.name}` created.'

        return self.render_to_response({'creation_form': creation_form, 'search_form': search_form, 'people': [], 'message': message})
