from django.urls import path
from . import views

app_name = "events"

event_common_urls = [
    path("", views.EventIndexView.as_view(), name="index"),
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
]

training_urls = [
    path(
        "<int:pk>/trenink/", views.TrainingDetailView.as_view(), name="detail_training"
    ),
    path("pridat/trenink/", views.TrainingCreateView.as_view(), name="add_training"),
    path(
        "<int:pk>/upravit/trenink/",
        views.TrainingUpdateView.as_view(),
        name="edit_training",
    ),
    path(
        "<int:pk>/trenink/upravit/vekove-omezeni/",
        views.EditMinAgeView.as_view(),
        name="edit_min_age_training",
    ),
]

one_time_event_urls = [
    path(
        "<int:pk>/jednorazova/",
        views.OneTimeEventDetailView.as_view(),
        name="detail_one_time_event",
    ),
    path(
        "pridat/jednorazova/",
        views.OneTimeEventCreateView.as_view(),
        name="add_one_time_event",
    ),
    path(
        "<int:pk>/upravit/jednorazova/",
        views.OneTimeEventUpdateView.as_view(),
        name="edit_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/pridat/osoba/",
        views.SignUpPersonForOneTimeEventView.as_view(),
        name="signup_person_for_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/odebrat/osoba/",
        views.RemoveParticipantFromOneTimeEventView.as_view(),
        name="remove_participant_from_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/pridat/nahradnik/",
        views.AddSubtituteForOneTimeEventView.as_view(),
        name="add_substitute_for_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/odebrat/nahradnik/",
        views.RemoveSubtituteForOneTimeEventView.as_view(),
        name="remove_substitute_from_one_time_event",
    ),
    path(
        "<int:event_id>/pridat/pozice/",
        views.EventPositionAssignmentCreateView.as_view(),
        name="add_position_assignment",
    ),
    path(
        "<int:event_id>/upravit/pozice/<int:pk>",
        views.EventPositionAssignmentUpdateView.as_view(),
        name="edit_position_assignment",
    ),
    path(
        "<int:event_id>/smazat/pozice/<int:pk>/",
        views.EventPositionAssignmentDeleteView.as_view(),
        name="delete_position_assignment",
    ),
    path(
        "<int:pk>/jednorazova/upravit/vekove-omezeni/",
        views.EditMinAgeView.as_view(),
        name="edit_min_age_one_time_event",
    ),
]

urlpatterns = event_common_urls + training_urls + one_time_event_urls
