from django.urls import reverse_lazy, reverse
from django.views import generic

from .forms import PersonForm, FeatureAssignmentForm
from .models import Person, FeatureAssignment


class IndexView(generic.ListView):
    model = Person
    template_name = "persons/index.html"
    context_object_name = "persons"


class DetailView(generic.DetailView):
    model = Person
    template_name = "persons/detail.html"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["qualifications"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type="K"
        )
        context["permissions"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type="O"
        )
        context["equipments"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type="V"
        )
        return context


class PersonCreateView(generic.edit.CreateView):
    model = Person
    template_name = "persons/edit.html"
    form_class = PersonForm


class PersonUpdateView(generic.edit.UpdateView):
    model = Person
    template_name = "persons/edit.html"
    form_class = PersonForm


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = "persons/confirm_delete.html"
    success_url = reverse_lazy("persons:index")


class FeatureAssignAddMixin(generic.edit.CreateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment_edit.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = None
        self.feature_type_name = None

    def form_valid(self, form):
        form.instance.person = Person.objects.get(
            id=self.kwargs["pk"]
        )  # TODO: process errors
        # TODO: add some message about success / failure
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FeatureAssignAddMixin, self).get_context_data(**kwargs)
        context["person"] = Person.objects.get(
            id=self.kwargs["pk"]
        )  # TODO: process errors
        context["type"] = self.feature_type_name
        return context


class QualificationAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = "K"
        self.feature_type_name = "kvalifikace"


class PermissionAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = "O"
        self.feature_type_name = "oprávnění"


class EquipmentAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = "V"
        self.feature_type_name = "vybavení"
