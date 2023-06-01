from django.urls import reverse_lazy
from django.views import generic

from .models import Person


class IndexView(generic.ListView):
    model = Person
    template_name = 'persons/index.html'
    context_object_name = 'persons'


class DetailView(generic.DetailView):
    model = Person
    template_name = 'persons/detail.html'


class PersonCreateView(generic.edit.CreateView):
    model = Person
    template_name = 'persons/edit.html'
    fields = ['email', 'first_name', 'last_name', 'date_of_birth', 'person_type']


class PersonUpdateView(generic.edit.UpdateView):
    model = Person
    template_name = 'persons/edit.html'
    fields = ['email', 'first_name', 'last_name', 'date_of_birth', 'person_type']


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = 'persons/confirm_delete.html'
    success_url = reverse_lazy("persons:index")
