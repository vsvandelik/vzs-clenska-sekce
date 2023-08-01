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
        "<int:position_id>/pridat/feature/",
        views.AddFeatureRequirementToPositionView.as_view(),
        name="add_feature",
    ),
    path(
        "<int:position_id>/smazat/feature/",
        views.RemoveFeatureRequirementToPositionView.as_view(),
        name="remove_feature",
    ),
    path(
        "<int:pk>/upravit/vekove-omezeni/",
        views.EditAgeLimitView.as_view(),
        name="edit_min_age",
    ),
    path(
        "<int:pk>/upravit/skupinu/",
        views.EditGroupMembershipView.as_view(),
        name="edit_group_membership",
    ),
    path(
        "<int:position_id>/pridat/typ-clenstvi/",
        views.AddAllowedPersonTypeToPositionView.as_view(),
        name="add_person_type",
    ),
    path(
        "<int:position_id>/smazat/typ-clenstvi/",
        views.RemoveAllowedPersonTypeFromPositionView.as_view(),
        name="remove_person_type",
    ),
]
