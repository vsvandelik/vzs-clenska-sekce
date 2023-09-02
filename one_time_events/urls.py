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
        name="edit-training-category",
    ),
    path(
        "<int:event_id>/pridat-prihlasku/",
        views.OneTimeEventParticipantEnrollmentCreateView.as_view(),
        name="create-participant-enrollment",
    ),
    path(
        "<int:event_id>/upravit-prihlasku/<int:pk>",
        views.OneTimeEventParticipantEnrollmentUpdateView.as_view(),
        name="edit-participant-enrollment",
    ),
    path(
        "<int:event_id>/smazat-prihlasku/<int:pk>",
        views.OneTimeEventParticipantEnrollmentDeleteView.as_view(),
        name="delete-participant-enrollment",
    ),
    path(
        "<int:event_id>/prihlasit-ucastnika/",
        views.OneTimeEventEnrollMyselfParticipantView.as_view(),
        name="enroll-myself-participant",
    ),
    path(
        "<int:occurrence_id>/pridat-organizatora-na-den",
        views.AddOrganizerForOccurrenceView.as_view(),
        name="add-organizer-for-occurrence",
    ),
    path(
        "<int:occurrence_id>/upravit-organizatora-na-den/<int:pk>",
        views.EditOrganizerForOccurrenceView.as_view(),
        name="edit-organizer-for-occurrence",
    ),
    path(
        "<int:occurrence_id>/smazat-organizatora-na-den/<int:pk>",
        views.DeleteOrganizerForOccurrenceView.as_view(),
        name="delete-organizer-from-occurrence",
    ),
    path(
        "<int:event_id>/hromadne-odebrani-organizatora/",
        views.BulkDeleteOrganizerFromOneTimeEventView.as_view(),
        name="bulk-delete-organizer",
    ),
    path(
        "<int:event_id>/hromadne-pridani-organizatora/",
        views.BulkAddOrganizerToOneTimeEventView.as_view(),
        name="bulk-add-organizer",
    ),
    path(
        "<int:event_id>/hromadne-schvalit",
        views.BulkApproveParticipantsView.as_view(),
        name="bulk-approve-participants",
    ),
]
