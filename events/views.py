from django.shortcuts import render, get_object_or_404, reverse
from .models import Event
from django.views import generic

# Create your views here.


class IndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"


def new_training(request):
    if request.method == "GET":
        return render(request, "events/edit-training.html")
    else:
        # TODO
        pass


def new_one_time_event(request):
    # TODO
    pass


def detail(request, event_id):
    # TODO
    pass
