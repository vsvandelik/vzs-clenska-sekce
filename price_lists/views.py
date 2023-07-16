from django.views import generic
from .models import PriceList
from django.urls import reverse_lazy


class PriceListIndexView(generic.ListView):
    model = PriceList
    template_name = "price_lists/index.html"
    context_object_name = "price_lists"


class PriceListCreateView(generic.CreateView):
    model = PriceList
    context_object_name = "price_list"
    template_name = "price_lists/create_edit.html"
    fields = ["name", "salary_base"]
    success_url = reverse_lazy("price_lists:index")


class PriceListUpdateView(generic.UpdateView):
    model = PriceList
    context_object_name = "price_list"
    template_name = "price_lists/create_edit.html"
    fields = ["name", "salary_base"]
    success_url = reverse_lazy("price_lists:index")


class PriceListDeleteView(generic.DeleteView):
    context_object_name = "price_list"
    model = PriceList
    template_name = "price_lists/delete.html"
    success_url = reverse_lazy("price_lists:index")


class PriceListDetailView(generic.DetailView):
    context_object_name = "price_list"
    model = PriceList
    template_name = "price_lists/detail.html"
