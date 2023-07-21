from django.views import generic

from events.mixin_extensions import MessagesMixin
from .models import PriceList
from django.urls import reverse_lazy, reverse
from .forms import BonusForm, PriceListBonus, PriceListForm
from django.shortcuts import get_object_or_404


class PriceListMixin:
    model = PriceList
    context_object_name = "price_list"


class PriceListCreateUpdateMixin(MessagesMixin, PriceListMixin):
    form_class = PriceListForm

    def get_success_url(self):
        return reverse("price_lists:detail", args=[self.object.id])


class PriceListIndexView(PriceListMixin, generic.ListView):
    template_name = "price_lists/index.html"
    context_object_name = "price_lists"

    def get_queryset(self):
        return PriceList.templates.all()


class PriceListCreateView(PriceListCreateUpdateMixin, generic.CreateView):
    template_name = "price_lists/create.html"
    success_message = "Ceník %(name)s úspěšně přidán"


class PriceListUpdateView(PriceListCreateUpdateMixin, generic.UpdateView):
    template_name = "price_lists/edit.html"
    success_message = "Ceník %(name)s úspěšně upraven"


class PriceListDeleteView(MessagesMixin, PriceListMixin, generic.DeleteView):
    template_name = "price_lists/delete.html"
    success_url = reverse_lazy("price_lists:index")

    def get_success_message(self, cleaned_data):
        return f"Ceník {self.object.name} úspěšně smazán"


class PriceListDetailView(generic.DetailView):
    context_object_name = "price_list"
    model = PriceList
    template_name = "price_lists/detail.html"


class BonusMixin(MessagesMixin):
    context_object_name = "bonus"
    model = PriceListBonus

    def get_success_url(self):
        return reverse("price_lists:detail", args=[self.kwargs["price_list_id"]])

    def get_context_data(self, **kwargs):
        kwargs.setdefault("price_list", self.price_list)
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.price_list = get_object_or_404(PriceList, pk=kwargs["price_list_id"])
        return super().dispatch(request, *args, **kwargs)


class BonusCreateUpdateMixin(BonusMixin):
    form_class = BonusForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["price_list"] = self.price_list
        return kwargs


class AddBonusToPriceListView(BonusCreateUpdateMixin, generic.CreateView):
    template_name = "price_lists/create_bonus.html"
    success_message = (
        "Příplatek %(extra_fee)s Kč za kvalifikaci %(feature)s úspěšně přidán"
    )


class EditBonusView(BonusCreateUpdateMixin, generic.UpdateView):
    template_name = "price_lists/edit_bonus.html"
    success_message = "Bonus úspěšně upraven"


class DeleteBonusView(BonusMixin, generic.DeleteView):
    template_name = "price_lists/delete_bonus.html"
    context_object_name = "bonus"
    model = PriceListBonus

    def get_success_message(self, cleaned_data):
        return f"Příplatek {self.object.extra_fee} Kč za kvalifikaci {self.object.feature} úspěšně smazán"

    def get_success_url(self):
        return reverse("price_lists:detail", args=[self.kwargs["price_list_id"]])

    def get_context_data(self, **kwargs):
        kwargs.setdefault("price_list", self.price_list)
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.price_list = get_object_or_404(PriceList, pk=kwargs["price_list_id"])
        return super().dispatch(request, *args, **kwargs)
