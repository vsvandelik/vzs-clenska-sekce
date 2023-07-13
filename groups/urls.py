from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupIndexView.as_view(), name="index"),
    path("<int:pk>/", views.StaticGroupDetailView.as_view(), name="detail"),
    path("pridat/staticka/", views.StaticGroupEditView.as_view(), name="add-static"),
    path(
        "<int:pk>/upravit/staticka/",
        views.StaticGroupEditView.as_view(),
        name="edit-static",
    ),
    path(
        "<int:group>/odebrat-clena/<int:person>/",
        views.StaticGroupRemoveMemberView.as_view(),
        name="remove-member",
    ),
    path("<int:pk>/smazat/", views.GroupDeleteView.as_view(), name="delete"),
    path(
        "synchronizovat-s-google/",
        views.SyncGroupMembersWithGoogleView.as_view(),
        name="sync-group-members-google",
    ),
    path(
        "<int:group>/synchronizovat-s-google/",
        views.SyncGroupMembersWithGoogleView.as_view(),
        name="sync-group-members-google",
    ),
]
