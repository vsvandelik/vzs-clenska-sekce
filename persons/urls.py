from django.urls import path, include

from features import views as features_views
from groups import views as groups_views
from transactions import views as transactions_views
from users import views as user_views
from . import views

app_name = "persons"

nested_feature_assigning_urls = [
    path("", features_views.FeatureAssignEditView.as_view(), name="add"),
    path("<int:pk>/", features_views.FeatureAssignEditView.as_view(), name="edit"),
    path(
        "<int:pk>/smazat/",
        features_views.FeatureAssignDeleteView.as_view(),
        name="delete",
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
        groups_views.AddPersonToGroupView.as_view(),
        name="add-to-group",
    ),
    path(
        "<int:pk>/odebrat-ze-skupiny/",
        groups_views.RemovePersonFromGroupView.as_view(),
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
    path(
        "<int:pk>/transakce/",
        transactions_views.TransactionListView.as_view(),
        name="transaction-list",
    ),
    path(
        "<int:person>/pridat-transakci/",
        transactions_views.TransactionCreateView.as_view(),
        name="transaction-add",
    ),
]
