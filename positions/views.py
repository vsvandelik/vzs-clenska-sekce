from django.urls import reverse_lazy
from .models import EventPosition
from django.views import generic
from django.shortcuts import reverse
from features.models import Feature
from .forms import AddFeatureRequirementToPositionForm, AgeLimitPositionForm
from events.mixin_extensions import MessagesMixin


class PositionMixin:
    model = EventPosition
    context_object_name = "position"


class PositionCreateUpdateMixin(PositionMixin):
    template_name = "positions/create_edit.html"
    fields = ["name"]


class PositionIndexView(PositionMixin, generic.ListView):
    template_name = "positions/index.html"
    context_object_name = "positions"


class PositionCreateView(PositionCreateUpdateMixin, generic.CreateView):
    success_url = reverse_lazy("positions:index")


class PositionUpdateView(PositionCreateUpdateMixin, generic.UpdateView):
    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class PositionDeleteView(PositionMixin, generic.DeleteView):
    template_name = "positions/delete.html"
    success_url = reverse_lazy("positions:index")


class PositionDetailView(PositionMixin, generic.DetailView):
    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("qualifications", Feature.qualifications.all())
        kwargs.setdefault(
            "qualifications_not_required",
            Feature.qualifications.all().difference(
                self.object.required_features.all()
            ),
        )
        kwargs.setdefault("permissions", Feature.permissions.all())
        kwargs.setdefault(
            "permissions_not_required",
            Feature.permissions.all().difference(self.object.required_features.all()),
        )
        kwargs.setdefault("equipment", Feature.equipments.all())
        kwargs.setdefault(
            "equipment_not_required",
            Feature.equipments.all().difference(self.object.required_features.all()),
        )
        return super().get_context_data(**kwargs)


class AddRemoveFeatureFromPosition(MessagesMixin, generic.FormView):
    form_class = AddFeatureRequirementToPositionForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.position.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position_id"] = self.kwargs["position_id"]
        return kwargs

    def _process_form(self, form, op):
        self.position = form.cleaned_data["position"]
        self.feature = form.cleaned_data["feature"]
        if op == "add":
            self.position.required_features.add(self.feature)
        else:
            self.position.required_features.remove(self.feature)
        self.position.save()


class AddFeatureRequirementToPositionView(AddRemoveFeatureFromPosition):
    def get_success_message(self, cleaned_data):
        return f"{self.feature.get_feature_type_display().capitalize()} {self.feature} přidána do pozice {self.position}"

    def form_valid(self, form):
        self._process_form(form, "add")
        return super().form_valid(form)


class RemoveFeatureRequirementToPositionView(AddRemoveFeatureFromPosition):
    def get_success_message(self, cleaned_data):
        return f"{self.feature.get_feature_type_display().capitalize()} {self.feature} odebrána z pozice {self.position}"

    def form_valid(self, form):
        self._process_form(form, "remove")
        return super().form_valid(form)


class EditAgeLimitView(PositionMixin, generic.UpdateView):
    template_name = "positions/edit_age_limit.html"
    form_class = AgeLimitPositionForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])
