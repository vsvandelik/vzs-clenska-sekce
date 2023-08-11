from django.shortcuts import render
from events.views import EventCreateMixin
from django.views import generic


# class TrainingDetailView(EventDetailViewMixin):
#     template_name = "events/training_detail.html"
#     invariant = lambda _, e: e.is_top_training
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context[self.context_object_name].extend_2_top_training()
#         return context
#
#
class TrainingCreateView(generic.CreateView, EventCreateMixin):
    template_name = "trainings/create.html"
    # form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = context["form"].generate_dates()
        return context


#
#
# class TrainingUpdateView(generic.UpdateView, EventUpdateMixin):
#     template_name = "events/edit_training.html"
#     form_class = TrainingForm
#     invariant = lambda _, e: e.is_top_training
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         event = context[self.context_object_name]
#         event.extend_2_top_training()
#         context["dates"] = context["form"].generate_dates()
#         return context
