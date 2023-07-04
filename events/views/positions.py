from django.urls import reverse_lazy
from ..models import EventPosition
from django.views import generic
from django.shortcuts import reverse
from persons.models import Feature
from ..forms import AddFeatureRequirementToPositionForm
from ..mixin_extensions import MessagesMixin


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

    def qualifications(self):
        return Feature.qualifications.all()

    def qualifications_not_required(self):
        return Feature.qualifications.all().difference(
            self.object.required_features.all()
        )

    def permissions(self):
        return Feature.permissions.all()

    def permissions_not_required(self):
        return Feature.permissions.all().difference(self.object.required_features.all())

    def equipment(self):
        return Feature.equipments.all()

    def equipment_not_required(self):
        return Feature.equipments.all().difference(self.object.required_features.all())


class AddRemoveFeatureFromPosition(MessagesMixin, generic.FormView):
    form_class = AddFeatureRequirementToPositionForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.position.id])

    def _process_form(self, form, op):
        fid = form.cleaned_data["feature_id"]
        pid = form.cleaned_data["position_id"]

        self.position = EventPosition.objects.get(pk=pid)
        self.feature = Feature.objects.get(pk=fid)
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
