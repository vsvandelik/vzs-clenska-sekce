from django.shortcuts import render
from django.views import generic

from .models import Person

class IndexView(generic.ListView):
    model = Person
    template_name = 'persons/index.html'
    context_object_name = 'persons'

class DetailView(generic.DetailView):
    model = Person
    template_name = 'persons/detail.html'
