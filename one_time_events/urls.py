from django.urls import path
from . import views

app_name = "one_time_events"

urlpatterns = [
    # path(
    #     "<int:pk>/",
    #     views.OneTimeEventDetailView.as_view(),
    #     name="detail",
    # ),
    path("pridat/", views.OneTimeEventCreateView.as_view(), name="add"),
    # path(
    #     "<int:pk>/upravit/",
    #     views.OneTimeEventUpdateView.as_view(),
    #     name="edit",
    # ),
    # path(
    #     "<int:event_id>/jednorazova/pridat/osoba/",
    #     views.EnrollParticipantForOneTimeEventView.as_view(),
    #     name="signup_person_for_one_time_event",
    # ),
    # path(
    #     "<int:event_id>/jednorazova/odebrat/osoba/",
    #     views.RemoveParticipantFromOneTimeEventView.as_view(),
    #     name="remove_participant_from_one_time_event",
    # ),
    # path(
    #     "<int:event_id>/jednorazova/pridat/nahradnik/",
    #     views.AddSubtituteForOneTimeEventView.as_view(),
    #     name="add_substitute_for_one_time_event",
    # ),
    # path(
    #     "<int:event_id>/jednorazova/odebrat/nahradnik/",
    #     views.RemoveSubtituteForOneTimeEventView.as_view(),
    #     name="remove_substitute_from_one_time_event",
    # ),
    # path(
    #     "<int:event_id>/pridat/pozice/",
    #     views.EventPositionAssignmentCreateView.as_view(),
    #     name="add_position_assignment",
    # ),
    # path(
    #     "<int:event_id>/upravit/pozice/<int:pk>",
    #     views.EventPositionAssignmentUpdateView.as_view(),
    #     name="edit_position_assignment",
    # ),
    # path(
    #     "<int:event_id>/smazat/pozice/<int:pk>/",
    #     views.EventPositionAssignmentDeleteView.as_view(),
    #     name="delete_position_assignment",
    # ),
]
