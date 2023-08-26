from django.urls import path

from . import views

app_name = "transactions"

urlpatterns = [
    path(
        "",
        views.TransactionIndexView.as_view(),
        name="index",
    ),
    path(
        "exportovat/",
        views.TransactionExportView.as_view(),
        name="export",
    ),
    path(
        "poslat-email/",
        views.TransactionSendEmailView.as_view(),
        name="send-email",
    ),
    path(
        "pridat-hromadne/",
        views.TransactionCreateBulkView.as_view(),
        name="add-bulk",
    ),
    path(
        "pridat-hromadne/potvrdit/",
        views.TransactionCreateBulkConfirmView.as_view(),
        name="add-bulk-confirm",
    ),
    path(
        "pridat/",
        views.TransactionCreateView.as_view(),
        name="add",
    ),
    path(
        "<int:pk>/qr/",
        views.TransactionQRView.as_view(),
        name="qr",
    ),
    path(
        "<int:pk>/upravit-z-osoby/",
        views.TransactionEditFromPersonView.as_view(),
        name="edit-from-person",
    ),
    path(
        "<int:pk>/upravit/",
        views.TransactionEditView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/smazat/",
        views.TransactionDeleteView.as_view(),
        name="delete",
    ),
    path(
        "moje/",
        views.MyTransactionsView.as_view(),
        name="my",
    ),
]
