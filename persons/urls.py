from django.urls import include, path

from features.views import (
    FeatureAssignDeleteView,
    FeatureAssignEditView,
    FeatureAssignReturnEquipmentView,
)
from groups.views import AddPersonToGroupView, RemovePersonFromGroupView
from transactions.views import (
    TransactionCreateBulkView,
    TransactionCreateFromPersonView,
    TransactionListView,
)
from users.views import (
    UserAssignPermissionView,
    UserChangePasswordOtherView,
    UserChangePasswordSelfView,
    UserCreatePasswordView,
    UserDeletePasswordView,
    UserGenerateNewPasswordView,
    UserRemovePermissionView,
)

from .views import (
    AddManagedPersonView,
    DeleteManagedPersonView,
    EditHourlyRateView,
    ExportSelectedPersonsView,
    MyProfileUpdateView,
    MyProfileView,
    PersonCreateChildParentView,
    PersonCreateChildView,
    PersonCreateView,
    PersonDeleteView,
    PersonDetailView,
    PersonIndexView,
    PersonStatsView,
    PersonUpdateView,
    SendEmailToSelectedPersonsView,
)

app_name = "persons"

my_profile_urlpatterns = [
    path("", MyProfileView.as_view(), name="index"),
    path("upravit/", MyProfileUpdateView.as_view(), name="edit"),
    path(
        "zmenit-heslo/",
        UserChangePasswordSelfView.as_view(),
        name="change-password",
    ),
]

nested_feature_assigning_urls = [
    path("", FeatureAssignEditView.as_view(), name="add"),
    path("<int:pk>/", FeatureAssignEditView.as_view(), name="edit"),
    path(
        "<int:pk>/smazat/",
        FeatureAssignDeleteView.as_view(),
        name="delete",
    ),
]

urlpatterns = [
    path("", PersonIndexView.as_view(), name="index"),
    path(
        "poslat-email/",
        SendEmailToSelectedPersonsView.as_view(),
        name="send-mail",
    ),
    path(
        "pridat-transakci/",
        TransactionCreateBulkView.as_view(),
        name="add-bulk-transaction",
        kwargs={"is_already_filtered": True},
    ),
    path("exportovat/", ExportSelectedPersonsView.as_view(), name="export"),
    path("pridat/", PersonCreateView.as_view(), name="add"),
    path("pridat-dite/", PersonCreateChildView.as_view(), name="add-child"),
    path(
        "pridat-dite/<int:pk>/pridat-rodice",
        PersonCreateChildParentView.as_view(),
        name="add-child-parent",
    ),
    path("<int:pk>/", PersonDetailView.as_view(), name="detail"),
    path("<int:pk>/statistiky", PersonStatsView.as_view(), name="stats"),
    path("<int:pk>/upravit/", PersonUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", PersonDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/ucet/pridat-heslo/",
        UserCreatePasswordView.as_view(),
        name="user-add-password",
    ),
    path(
        "<int:pk>/ucet/smazat-heslo/",
        UserDeletePasswordView.as_view(),
        name="user-delete-password",
    ),
    path(
        "<int:pk>/ucet/zmenit-heslo/",
        UserChangePasswordOtherView.as_view(),
        name="user-change-password-other",
    ),
    path(
        "<int:pk>/ucet/generovat-nove-heslo/",
        UserGenerateNewPasswordView.as_view(),
        name="user-generate-new-password",
    ),
    path(
        "<int:pk>/ucet/pridat-povoleni/",
        UserAssignPermissionView.as_view(),
        name="user-assign-permission",
    ),
    path(
        "<int:pk>/ucet/odebrat-povoleni/",
        UserRemovePermissionView.as_view(),
        name="user-remove-permission",
    ),
    path(
        "<int:pk>/pridat-spravovanou-osobu/",
        AddManagedPersonView.as_view(),
        name="add-managed-person",
    ),
    path(
        "<int:pk>/odebrat-spravovanou-osobu/",
        DeleteManagedPersonView.as_view(),
        name="remove-managed-person",
    ),
    path(
        "<int:pk>/hodinove-sazby/",
        EditHourlyRateView.as_view(),
        name="edit-hourly-rates",
    ),
    path(
        "<int:pk>/pridat-do-skupiny/",
        AddPersonToGroupView.as_view(),
        name="add-to-group",
    ),
    path(
        "<int:pk>/odebrat-ze-skupiny/",
        RemovePersonFromGroupView.as_view(),
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
        "<int:person>/vybaveni/<int:pk>/vratit/",
        FeatureAssignReturnEquipmentView.as_view(),
        {"feature_type": "equipments"},
        name="equipments-return",
    ),
    path(
        "<int:person>/vybaveni/",
        include((nested_feature_assigning_urls, "equipments")),
        {"feature_type": "equipments"},
    ),
    path(
        "<int:pk>/transakce/",
        TransactionListView.as_view(),
        name="transaction-list",
    ),
    path(
        "<int:person>/pridat-transakci/",
        TransactionCreateFromPersonView.as_view(),
        name="transaction-add",
    ),
]
