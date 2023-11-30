from django.urls import path

from groups.views import (
    GroupAddMembersView,
    GroupCreateView,
    GroupDeleteView,
    GroupDetailView,
    GroupEditView,
    GroupIndexView,
    GroupRemoveMemberView,
    SyncGroupMembersWithGoogleAllView,
    SyncGroupMembersWithGoogleView,
)

app_name = "groups"

urlpatterns = [
    path("", GroupIndexView.as_view(), name="index"),
    path("<int:pk>/", GroupDetailView.as_view(), name="detail"),
    path("pridat/", GroupCreateView.as_view(), name="add"),
    path("<int:pk>/upravit/", GroupEditView.as_view(), name="edit"),
    path("<int:pk>/pridat-cleny/", GroupAddMembersView.as_view(), name="add-members"),
    path(
        "<int:group_id>/odebrat-clena/<int:person_id>/",
        GroupRemoveMemberView.as_view(),
        name="remove-member",
    ),
    path("<int:pk>/smazat/", GroupDeleteView.as_view(), name="delete"),
    path(
        "synchronizovat-s-google/",
        SyncGroupMembersWithGoogleAllView.as_view(),
        name="sync-group-members-google",
    ),
    path(
        "<int:group_id>/synchronizovat-s-google/",
        SyncGroupMembersWithGoogleView.as_view(),
        name="sync-group-members-google",
    ),
]
