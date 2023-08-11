from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventIndexView.as_view(), name="index"),
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
    # path(
    #     "<int:pk>/upravit/vekove-omezeni/",
    #     views.EditMinAgeView.as_view(),
    #     name="edit_min_age",
    # ),
    # path(
    #     "<int:pk>/upravit/skupinu/",
    #     views.EditGroupMembershipView.as_view(),
    #     name="edit_group_membership",
    # ),
    # path(
    #     "<int:event_id>/pridat/typ-clenstvi/",
    #     views.AddAllowedPersonTypeToEventView.as_view(),
    #     name="add_person_type",
    # ),
    # path(
    #     "<int:event_id>/smazat/typ-clenstvi/",
    #     views.RemoveAllowedPersonTypeFromEventView.as_view(),
    #     name="remove_person_type",
    # ),
]
