from django.urls import path, include
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
        "<int:event_id>/jednorazova/pridat/nahradnik",
        views.AddSubtituteForOneTimeEventView.as_view(),
        name="add_substitute_for_one_time_event",
    ),
    path(
        "<int:event_id>/jednorazova/odebrat/nahradnik/",
        views.RemoveSubtituteForOneTimeEventView.as_view(),
        name="remove_substitute_from_one_time_event",
    ),
]

urlpatterns = event_common_urls + training_urls + one_time_event_urls
positions_urls = [
    path("", views.PositionIndexView.as_view(), name="index"),
    path("pridat/", views.PositionCreateView.as_view(), name="add"),
    path("<int:pk>/upravit/", views.PositionUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.PositionDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.PositionDetailView.as_view(), name="detail"),
    path(
        "<int:position_id>/pridat/feature",
        views.AddFeatureRequirementToPositionView.as_view(),
        name="add_feature",
    ),
    path(
        "<int:position_id>/smazat/feature",
        views.RemoveFeatureRequirementToPositionView.as_view(),
        name="remove_feature",
    ),
]
