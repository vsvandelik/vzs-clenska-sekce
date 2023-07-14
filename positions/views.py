from django.urls import reverse_lazy
from .models import EventPosition
from django.views import generic
from django.shortcuts import reverse
from features.models import Feature
from persons.models import Person
from .models import PersonType
from .forms import (
    AddFeatureRequirementToPositionForm,
    AgeLimitForm,
    GroupMembershipForm,
    PersonTypeForm,
)
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
            "qualifications_required", self.object.required_features.all()
        )
        kwargs.setdefault("permissions", Feature.permissions.all())
        kwargs.setdefault("permissions_required", self.object.required_features.all())
        kwargs.setdefault("equipment", Feature.equipments.all())
        kwargs.setdefault("equipment_required", self.object.required_features.all())
        kwargs.setdefault("available_person_types", Person.Type.choices)
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
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


class EditAgeLimitView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "positions/edit_age_limit.html"
    form_class = AgeLimitForm
    success_message = "Změna věkového omezení uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class EditGroupMembershipView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "positions/edit_group_membership.html"
    form_class = GroupMembershipForm
    success_message = "Změna členství ve skupině uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class AddOrRemoveAllowedPersonTypeToPositionView(MessagesMixin, generic.FormView):
    form_class = PersonTypeForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.position.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position_id"] = self.kwargs["position_id"]
        return kwargs

    def _process_form(self, form, op):
        self.position = form.cleaned_data["position"]
        person_type = form.cleaned_data["person_type"]
        try:
            self.person_type_obj = PersonType.objects.get(person_type=person_type)
        except PersonType.DoesNotExist:
            self.person_type_obj = PersonType(person_type=person_type)
            self.person_type_obj.save()
        if op == "add":
            self.position.allowed_person_types.add(self.person_type_obj.pk)
        else:
            self.position.allowed_person_types.remove(self.person_type_obj.pk)
        self.position.save()


class AddAllowedPersonTypeToPositionView(AddOrRemoveAllowedPersonTypeToPositionView):
    def form_valid(self, form):
        self._process_form(form, "add")
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return f"Omezení pro typ členství {self.person_type_obj.get_person_type_display()} přidáno do pozice"


class RemoveAllowedPersonTypeFromPositionView(
    AddOrRemoveAllowedPersonTypeToPositionView
):
    def form_valid(self, form):
        self._process_form(form, "remove")
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return f"Omezení pro typ členství {self.person_type_obj.get_person_type_display()} smazáno z pozice"
