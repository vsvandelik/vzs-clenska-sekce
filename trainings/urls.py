from django.urls import path

from transactions import views as transactions_views
from . import views

app_name = "trainings"

urlpatterns = [
    path("<int:pk>/", views.TrainingDetailView.as_view(), name="detail"),
    path("pridat/", views.TrainingCreateView.as_view(), name="add"),
    path(
        "<int:pk>/upravit/",
        views.TrainingUpdateView.as_view(),
        name="edit",
    ),
    path(
        "<int:event_id>/pridat-nahradu/",
        views.TrainingAddReplaceableTrainingView.as_view(),
        name="add-replaceable-training",
    ),
    path(
        "<int:event_id>/odebrat-nahradu/",
        views.TrainingRemoveReplaceableTrainingView.as_view(),
        name="remove-replaceable-training",
    ),
    path(
        "<int:event_id>/pridat-prihlasku/",
        views.TrainingParticipantEnrollmentCreateView.as_view(),
        name="create-participant-enrollment",
    ),
    path(
        "<int:event_id>/upravit-prihlasku/<int:pk>",
        views.TrainingParticipantEnrollmentUpdateView.as_view(),
        name="edit-participant-enrollment",
    ),
    path(
        "<int:event_id>/smazat-prihlasku/<int:pk>",
        views.TrainingParticipantEnrollmentDeleteView.as_view(),
        name="delete-participant-enrollment",
    ),
    path(
        "<int:event_id>/prihlasit-ucastnika/",
        views.TrainingEnrollMyselfParticipantView.as_view(),
        name="enroll-myself-participant",
    ),
    path(
        "<int:event_id>/pridat-trenera/",
        views.CoachAssignmentCreateView.as_view(),
        name="create-coach-assignment",
    ),
    path(
        "<int:event_id>/upravit-trenera/<int:pk>",
        views.CoachAssignmentUpdateView.as_view(),
        name="edit-coach-assignment",
    ),
    path(
        "<int:event_id>/odebrat-trenera/<int:pk>",
        views.CoachAssignmentDeleteView.as_view(),
        name="delete-coach-assignment",
    ),
    path(
        "<int:event_id>/pridat-transakci/",
        transactions_views.TransactionAddTrainingPaymentView.as_view(),
        name="add-transaction",
    ),
    path(
        "<int:event_id>/pridat-transakci/potvrdit",
        transactions_views.TransactionCreateTrainingBulkConfirmView.as_view(),
        name="add-transaction-confirm",
    ),
    path(
        "<int:pk>/hromadne-schvalit",
        views.TrainingBulkApproveParticipantsView.as_view(),
        name="bulk-approve-participants",
    ),
    path(
        "<int:event_id>/detail-dne/<int:pk>/",
        views.TrainingOccurrenceDetailView.as_view(),
        name="occurrence-detail",
    ),
    path(
        "<int:event_id>/detail-dne/<int:occurrence_id>/zrusit-omluveni-trenera/<int:pk>/",
        views.CancelCoachExcuseView.as_view(),
        name="cancel-coach-excuse",
    ),
    path(
        "<int:event_id>/detail-dne/<int:occurrence_id>/omluvit-moji-neucast-trener/",
        views.ExcuseMyselfCoachView.as_view(),
        name="excuse-myself-coach",
    ),
    path(
        "<int:event_id>/detail-dne/<int:occurrence_id>/omluvit-trenera/<int:pk>/",
        views.CoachExcuseView.as_view(),
        name="excuse-coach",
    ),
    path(
        "<int:event_id>/detail-dne/<int:occurrence_id>/prihlasit-se-jednorazove-trener/",
        views.EnrollMyselfOrganizerForOccurrence.as_view(),
        name="enroll-myself-organizer-occurrence",
    ),
]
