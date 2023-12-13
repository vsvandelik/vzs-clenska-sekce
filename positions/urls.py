from django.urls import path

from .views import (
    AddFeatureRequirementPositionView,
    AddRemoveAllowedPersonTypeToPositionView,
    EditAgeLimitView,
    EditGroupMembershipView,
    PositionCreateView,
    PositionDeleteView,
    PositionDetailView,
    PositionIndexView,
    PositionUpdateView,
    RemoveFeatureRequirementPositionView,
)

app_name = "positions"

urlpatterns = [
    path("", PositionIndexView.as_view(), name="index"),
    path("pridat/", PositionCreateView.as_view(), name="add"),
    path("<int:pk>/upravit/", PositionUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", PositionDeleteView.as_view(), name="delete"),
    path("<int:pk>/", PositionDetailView.as_view(), name="detail"),
    path(
        "<int:pk>/pridat-feature/",
        AddFeatureRequirementPositionView.as_view(),
        name="add-feature",
    ),
    path(
        "<int:pk>/odebrat-feature/",
        RemoveFeatureRequirementPositionView.as_view(),
        name="remove-feature",
    ),
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
        AddRemoveAllowedPersonTypeToPositionView.as_view(),
        name="add-person-type",
    ),
    path(
        "<int:pk>/odebrat-typ-clenstvi/",
        AddRemoveAllowedPersonTypeToPositionView.as_view(),
        name="remove-person-type",
    ),
]
