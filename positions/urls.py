from django.urls import path
from . import views

app_name = "positions"

urlpatterns = [
    path("", views.PositionIndexView.as_view(), name="index"),
    path("pridat/", views.PositionCreateView.as_view(), name="add"),
    path("<int:pk>/upravit/", views.PositionUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.PositionDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.PositionDetailView.as_view(), name="detail"),
    path(
        "<int:pk>/pridat-feature/",
        views.AddRemoveFeatureRequirementPositionView.as_view(),
        name="add_feature",
    ),
    path(
        "<int:pk>/odebrat-feature/",
        views.AddRemoveFeatureRequirementPositionView.as_view(),
        name="remove_feature",
    ),
    path(
        "<int:pk>/upravit-vekove-omezeni/",
        views.EditAgeLimitView.as_view(),
        name="edit_age_limit",
    ),
    path(
        "<int:pk>/upravit-skupinu/",
        views.EditGroupMembershipView.as_view(),
        name="edit_group_membership",
    ),
    path(
        "<int:pk>/pridat-typ-clenstvi/",
        views.AddRemoveAllowedPersonTypeToPositionView.as_view(),
        name="add_person_type",
    ),
    path(
        "<int:pk>/odebrat-typ-clenstvi/",
        views.AddRemoveAllowedPersonTypeToPositionView.as_view(),
        name="remove_person_type",
    ),
]
