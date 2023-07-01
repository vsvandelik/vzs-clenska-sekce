from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventIndexView.as_view(), name="index"),
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/jednorazova/",
        views.OneTimeEventDetailView.as_view(),
        name="detail_one_time_event",
    ),
    path(
        "<int:pk>/trenink/", views.TrainingDetailView.as_view(), name="detail_training"
    ),
    path("pridat/trenink/", views.TrainingCreateView.as_view(), name="add_training"),
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
        "<int:pk>/upravit/trenink/",
        views.TrainingUpdateView.as_view(),
        name="edit_training",
    ),
    path(
        "<int:event_id>/jednorazova/pridat/osoba/",
        views.SignUpPersonForOneTimeEvent.as_view(),
        name="signup_person_for_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/odebrat/osoba/",
        views.RemoveParticipantFromOneTimeEvent.as_view(),
        name="remove_participant_from_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/pridat/nahradnik",
        views.AddSubtituteForOneTimeEvent.as_view(),
        name="add_substitute_for_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/odebrat/nahradnik/",
        views.RemoveSubtituteForOneTimeEvent.as_view(),
        name="remove_substitute_from_one_time_event",
    ),
]
