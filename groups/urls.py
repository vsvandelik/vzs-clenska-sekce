from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupIndexView.as_view(), name="index"),
    path("<int:pk>/", views.GroupDetailView.as_view(), name="detail"),
    path("pridat/", views.GroupEditView.as_view(), name="add"),
    path(
        "<int:pk>/upravit/",
        views.GroupEditView.as_view(),
        name="edit",
    ),
    path(
        "<int:group>/odebrat-clena/<int:person>/",
        views.GroupRemoveMemberView.as_view(),
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
