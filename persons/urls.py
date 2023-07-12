from django.urls import path, include

from users import views as user_views
from . import views

app_name = "persons"

feature_urls = [
    path("", views.FeatureIndexView.as_view(), name="index"),
    path("pridat/", views.FeatureEditView.as_view(), name="add"),
    path("<int:pk>/", views.FeatureDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit/", views.FeatureEditView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.FeatureDeleteView.as_view(), name="delete"),
]

nested_feature_assigning_urls = [
    path("", views.FeatureAssignEditView.as_view(), name="add"),
    path("<int:pk>/", views.FeatureAssignEditView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.FeatureAssignDeleteView.as_view(), name="delete"),
]

groups_urlpatterns = [
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

urlpatterns = [
    path("", views.PersonIndexView.as_view(), name="index"),
    path(
        "poslat-email/",
        views.SendEmailToSelectedPersonsView.as_view(),
        name="send-mail",
    ),
    path("exportovat/", views.ExportSelectedPersonsView.as_view(), name="export"),
    path("pridat/", views.PersonCreateView.as_view(), name="add"),
    path("<int:pk>/", views.PersonDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit/", views.PersonUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.PersonDeleteView.as_view(), name="delete"),
    path("<int:pk>/ucet/pridat/", user_views.UserCreateView.as_view(), name="user-add"),
    path(
        "<int:pk>/ucet/smazat/", user_views.UserDeleteView.as_view(), name="user-delete"
    ),
    path(
        "<int:pk>/ucet/zmenit-heslo/",
        user_views.UserChangePasswordView.as_view(),
        name="user-change-password",
    ),
    path(
        "<int:pk>/ucet/generovat-nove-heslo/",
        user_views.UserGenerateNewPasswordView.as_view(),
        name="user-generate-new-password",
    ),
    path(
        "<int:pk>/ucet/pridat-povoleni/",
        user_views.UserAssignPermissionView.as_view(),
        name="user-assign-permission",
    ),
    path(
        "<int:pk>/ucet/odebrat-povoleni/",
        user_views.UserRemovePermissionView.as_view(),
        name="user-remove-permission",
    ),
    path(
        "<int:pk>/pridat-spravovanou-osobu/",
        views.AddManagedPersonView.as_view(),
        name="add-managed-person",
    ),
    path(
        "<int:pk>/odebrat-spravovanou-osobu/",
        views.DeleteManagedPersonView.as_view(),
        name="remove-managed-person",
    ),
    path(
        "<int:pk>/pridat-do-skupiny/",
        views.AddPersonToGroupView.as_view(),
        name="add-to-group",
    ),
    path(
        "<int:pk>/odebrat-ze-skupiny/",
        views.RemovePersonFromGroupView.as_view(),
        name="remove-from-group",
    ),
    path(
        "<int:person>/kvalifikace/",
        include((nested_feature_assigning_urls, "qualifications")),
        {"feature_type": "qualifications"},
    ),
    path(
        "<int:person>/opravneni/",
        include((nested_feature_assigning_urls, "permissions")),
        {"feature_type": "permissions"},
    ),
    path(
        "<int:person>/vybaveni/",
        include((nested_feature_assigning_urls, "equipments")),
        {"feature_type": "equipments"},
    ),
    path("skupiny/", include((groups_urlpatterns, "groups"))),
    path(
        "<int:pk>/transakce/",
        views.TransactionListView.as_view(),
        name="transaction-list",
    ),
    path(
        "<int:person>/pridat-transakci/",
        views.TransactionCreateView.as_view(),
        name="transaction-add",
    ),
    path(
        "transakce/<int:pk>/qr/",
        views.TransactionQRView.as_view(),
        name="transaction-qr",
    ),
    path(
        "transakce/<int:pk>/upravit/",
        views.TransactionEditView.as_view(),
        name="transaction-edit",
    ),
    path(
        "transakce/<int:pk>/smazat/",
        views.TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
]
