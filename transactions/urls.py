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
        "<int:pk>/qr/",
        views.TransactionQRView.as_view(),
        name="qr",
    ),
    path(
        "pridat/",
        views.TransactionCreateView.as_view(),
        name="edit",
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
]
