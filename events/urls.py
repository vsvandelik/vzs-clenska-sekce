from django.urls import path

from .views import (
    AddRemoveAllowedPersonTypeView,
    EditAgeLimitView,
    EditGroupMembershipView,
    EventDeleteView,
    EventPositionAssignmentCreateView,
    EventPositionAssignmentDeleteView,
    EventPositionAssignmentUpdateView,
    UnenrollMyselfParticipantView,
)

app_name = "events"

urlpatterns = [
    path("<int:pk>/smazat/", EventDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/upravit-vekove-omezeni/",
        EditAgeLimitView.as_view(),
        name="edit-age-limit",
    ),
    path(
        "<int:pk>/upravit-skupinu/",
        EditGroupMembershipView.as_view(),
        name="edit-group-membership",
    ),
    path(
        "<int:pk>/pridat-typ-clenstvi/",
        AddRemoveAllowedPersonTypeView.as_view(),
        name="add-person-type",
    ),
    path(
        "<int:pk>/odebrat-typ-clenstvi/",
        AddRemoveAllowedPersonTypeView.as_view(),
        name="remove-person-type",
    ),
    path(
        "<int:event_id>/pridat-pozici/",
        EventPositionAssignmentCreateView.as_view(),
        name="add-position-assignment",
    ),
    path(
        "<int:event_id>/upravit-pozici/<int:pk>",
        EventPositionAssignmentUpdateView.as_view(),
        name="edit-position-assignment",
    ),
    path(
        "<int:event_id>/odebrat-pozici/<int:pk>/",
        EventPositionAssignmentDeleteView.as_view(),
        name="delete-position-assignment",
    ),
    path(
        "<int:pk>/odhlasit-ucastnika/",
        UnenrollMyselfParticipantView.as_view(),
        name="unenroll-myself-participant",
    ),
]
