from django.urls import path
from . import views

app_name = "one_time_events"

urlpatterns = [
    path(
        "<int:pk>/",
        views.OneTimeEventDetailView.as_view(),
        name="detail",
    ),
    path("pridat/", views.OneTimeEventCreateView.as_view(), name="add"),
    path(
        "<int:pk>/upravit/",
        views.OneTimeEventUpdateView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/upravit-dochazku-treninku",
        views.EditTrainingCategoryView.as_view(),
        name="edit_training_category",
    ),
    path(
        "<int:event_id>/pridat-prihlasku/",
        views.OneTimeEventParticipantEnrollmentCreateView.as_view(),
        name="create_participant_enrollment",
    ),
    path(
        "<int:event_id>/upravit-prihlasku/<int:pk>",
        views.OneTimeEventParticipantEnrollmentUpdateView.as_view(),
        name="edit_participant_enrollment",
    ),
    path(
        "<int:event_id>/smazat-prihlasku/<int:pk>",
        views.OneTimeEventParticipantEnrollmentDeleteView.as_view(),
        name="delete_participant_enrollment",
    ),
]
