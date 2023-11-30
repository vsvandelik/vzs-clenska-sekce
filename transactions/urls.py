from django.urls import path

from .views import (
    BulkTransactionDeleteView,
    TransactionCreateBulkView,
    TransactionCreateSameAmountBulkConfirmView,
    TransactionCreateView,
    TransactionDeleteView,
    TransactionEditFromPersonView,
    TransactionEditView,
    TransactionExportView,
    TransactionIndexView,
    TransactionQRView,
    TransactionSendEmailView,
)

app_name = "transactions"

urlpatterns = [
    path(
        "",
        TransactionIndexView.as_view(),
        name="index",
    ),
    path(
        "exportovat/",
        TransactionExportView.as_view(),
        name="export",
    ),
    path(
        "poslat-email/",
        TransactionSendEmailView.as_view(),
        name="send-email",
    ),
    path(
        "pridat-hromadne/",
        TransactionCreateBulkView.as_view(),
        name="add-bulk",
    ),
    path(
        "pridat-hromadne/potvrdit/",
        TransactionCreateSameAmountBulkConfirmView.as_view(),
        name="add-bulk-confirm",
    ),
    path(
        "pridat/",
        TransactionCreateView.as_view(),
        name="add",
    ),
    path(
        "<int:pk>/qr/",
        TransactionQRView.as_view(),
        name="qr",
    ),
    path(
        "<int:pk>/upravit-z-osoby/",
        TransactionEditFromPersonView.as_view(),
        name="edit-from-person",
    ),
    path(
        "<int:pk>/upravit/",
        TransactionEditView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/smazat/",
        TransactionDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<int:pk>/smazat-hromadnou/",
        BulkTransactionDeleteView.as_view(),
        name="delete-bulk",
    ),
]
