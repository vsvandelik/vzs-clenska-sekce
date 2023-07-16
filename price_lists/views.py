from django.views import generic
from .models import PriceList
from django.urls import reverse_lazy
from .forms import AddBonusForm
from django.shortcuts import get_object_or_404


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


class AddBonusToPriceListView(generic.CreateView):
    context_object_name = "bonus"
    form_class = AddBonusForm
    template_name = "price_lists/create_edit_bonus.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("price_list", self.price_list)
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["price_list"] = self.price_list
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.price_list = get_object_or_404(PriceList, pk=kwargs["price_list_id"])
        return super().dispatch(request, *args, **kwargs)


class EditBonusPriceListView(generic.UpdateView):
    pass
