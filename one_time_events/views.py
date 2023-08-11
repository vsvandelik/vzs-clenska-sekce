from django.shortcuts import render
from events.views import EventCreateMixin
from django.views import generic


#
# class OneTimeEventDetailView(EventDetailViewMixin):
#     template_name = "events/one_time_event_detail.html"
#     invariant = lambda _, e: e.is_one_time_event
#
#     def get_context_data(self, **kwargs):
#         kwargs.setdefault("persons", Person.objects.all())
#         kwargs.setdefault(
#             "event_participation",
#             EventOccurrenceParticipation.objects.filter(event=self.object).all(),
#         )
#         kwargs.setdefault(
#             "event_participation_approved",
#             EventOccurrenceParticipation.objects.filter(
#                 event=self.object, state=Participation.State.APPROVED
#             ),
#         )
#         kwargs.setdefault(
#             "event_participation_substitute",
#             EventOccurrenceParticipation.objects.filter(
#                 event=self.object, state=Participation.State.SUBSTITUTE
#             ),
#         )
#         return super().get_context_data(**kwargs)
#
#
class OneTimeEventCreateView(generic.CreateView, EventCreateMixin):
    template_name = "one_time_events/create_edit.html"
    # form_class = OneTimeEventForm


#
#
# class OneTimeEventUpdateView(generic.UpdateView, EventUpdateMixin):
#     template_name = "events/edit_one_time_event.html"
#     form_class = OneTimeEventForm
#     invariant = lambda _, e: e.is_one_time_event
#
#     def get(self, request, *args, **kwargs):
#         event = get_object_or_404(Event, pk=kwargs["pk"])
#         event.set_type()
#         if not event.is_one_time_event:
#             return redirect(self.success_url)
#         return super().get(request, *args, **kwargs)
