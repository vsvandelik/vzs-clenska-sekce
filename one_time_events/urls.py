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
        "<int:pk>/upravit/dochazka-trenink",
        views.EditTrainingCategoryView.as_view(),
        name="edit_training_category",
    ),
    path(
        "<int:event_id>/pridat/prihlasku/",
        views.ParticipantEnrollmentCreateView.as_view(),
        name="create_participant_enrollment",
    ),
]
