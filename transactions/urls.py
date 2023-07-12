from django.urls import path

from . import views

app_name = "transactions"

urlpatterns = [
    path(
        "<int:pk>/qr/",
        views.TransactionQRView.as_view(),
        name="qr",
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
