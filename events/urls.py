from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/upravit-vekove-omezeni/",
        views.EditAgeLimitView.as_view(),
        name="edit-age-limit",
    ),
    path(
        "<int:pk>/upravit-skupinu/",
        views.EditGroupMembershipView.as_view(),
        name="edit-group-membership",
    ),
    path(
        "<int:pk>/pridat-typ-clenstvi/",
        views.AddRemoveAllowedPersonTypeView.as_view(),
        name="add-person-type",
    ),
    path(
        "<int:pk>/odebrat-typ-clenstvi/",
        views.AddRemoveAllowedPersonTypeView.as_view(),
        name="remove-person-type",
    ),
    path(
        "<int:event_id>/pridat-pozici/",
        views.EventPositionAssignmentCreateView.as_view(),
        name="add-position-assignment",
    ),
    path(
        "<int:event_id>/upravit-pozici/<int:pk>",
        views.EventPositionAssignmentUpdateView.as_view(),
        name="edit-position-assignment",
    ),
    path(
        "<int:event_id>/odebrat-pozici/<int:pk>/",
        views.EventPositionAssignmentDeleteView.as_view(),
        name="delete-position-assignment",
    ),
    path(
        "<int:pk>/odhlasit-ucastnika/",
        views.UnenrollMyselfParticipantView.as_view(),
        name="unenroll-myself-participant",
    ),
]
