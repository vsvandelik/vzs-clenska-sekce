from django.urls import reverse_lazy
from .models import EventPosition
from django.views import generic
from django.shortcuts import reverse
from django.core.exceptions import ImproperlyConfigured
from features.models import Feature
from persons.models import PersonType
from .forms import (
    AddFeatureRequirementToPositionForm,
    PositionAgeLimitForm,
    PositionGroupMembershipForm,
    PositionAllowedPersonTypeForm,
)
from vzs.mixin_extensions import MessagesMixin
from events.views import PersonTypeDetailViewMixin


class PositionMixin:
    model = EventPosition
    context_object_name = "position"


class PositionCreateUpdateMixin(MessagesMixin, PositionMixin):
    template_name = "positions/create_edit.html"
    fields = ["name"]

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class PositionIndexView(PositionMixin, generic.ListView):
    template_name = "positions/index.html"
    context_object_name = "positions"


class PositionCreateView(PositionCreateUpdateMixin, generic.CreateView):
    template_name = "positions/create.html"
    success_message = "Pozice %(name)s úspěšně přidána"


class PositionUpdateView(PositionCreateUpdateMixin, generic.UpdateView):
    template_name = "positions/edit.html"
    success_message = "Pozice %(name)s úspěšně upravena"


class PositionDeleteView(MessagesMixin, PositionMixin, generic.DeleteView):
    template_name = "positions/delete.html"
    success_url = reverse_lazy("positions:index")

    def get_success_message(self, cleaned_data):
        return f"Pozice {self.object.name} úspěšně smazána"


class PositionDetailView(PositionMixin, PersonTypeDetailViewMixin, generic.DetailView):
    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("qualifications", Feature.qualifications.all())
        kwargs.setdefault(
            "qualifications_required", self.object.required_features.all()
        )
        kwargs.setdefault("permissions", Feature.permissions.all())
        kwargs.setdefault("permissions_required", self.object.required_features.all())
        kwargs.setdefault("equipment", Feature.equipments.all())
        kwargs.setdefault("equipment_required", self.object.required_features.all())
        return super().get_context_data(**kwargs)


class AddRemoveFeatureFromPosition(MessagesMixin, generic.FormView):
    form_class = AddFeatureRequirementToPositionForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.kwargs["position_id"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position_id"] = self.kwargs["position_id"]
        return kwargs

    def _change_db(self, position, feature):
        raise ImproperlyConfigured("This method should never be called")

    def form_valid(self, form):
        position = form.cleaned_data["position"]
        feature = form.cleaned_data["feature"]
        self._change_db(position, feature)
        position.save()
        return super().form_valid(form)


class AddFeatureRequirementToPositionView(AddRemoveFeatureFromPosition):
    def get_success_message(self, cleaned_data):
        p = cleaned_data["position"]
        f = cleaned_data["feature"]
        return f"{f.get_feature_type_display().capitalize()} {f} přidána do pozice {p}"

    def _change_db(self, position, feature):
        position.required_features.add(feature)


class RemoveFeatureRequirementToPositionView(AddRemoveFeatureFromPosition):
    def get_success_message(self, cleaned_data):
        p = cleaned_data["position"]
        f = cleaned_data["feature"]
        return f"{f.get_feature_type_display().capitalize()} {f} odebrána z pozice {p}"

    def _change_db(self, position, feature):
        position.required_features.remove(feature)


class EditAgeLimitView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "events/edit_age_limit.html"
    form_class = PositionAgeLimitForm
    success_message = "Změna věkového omezení uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class EditGroupMembershipView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "events/edit_group_membership.html"
    form_class = PositionGroupMembershipForm
    success_message = "Změna členství ve skupině uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class AddRemoveAllowedPersonTypeToPositionView(MessagesMixin, generic.UpdateView):
    form_class = PositionAllowedPersonTypeForm
    model = EventPosition

    def get_success_url(self):
        return reverse("positions:detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = EventPosition.objects.get(pk=self.kwargs["pk"])
        return kwargs
