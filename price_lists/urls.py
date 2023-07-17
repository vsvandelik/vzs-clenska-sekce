from django.urls import path
from . import views

app_name = "price_lists"

urlpatterns = [
    path("", views.PriceListIndexView.as_view(), name="index"),
    path("pridat/", views.PriceListCreateView.as_view(), name="add"),
    path("<int:pk>/upravit/", views.PriceListUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.PriceListDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.PriceListDetailView.as_view(), name="detail"),
    path(
        "<int:price_list_id>/pridat/bonus",
        views.AddBonusToPriceListView.as_view(),
        name="add_bonus",
    ),
    path(
        "<int:price_list_id>/upravit/<int:pk>/bonus",
        views.EditBonusView.as_view(),
        name="edit_bonus",
    ),
    path(
        "<int:price_list_id>/smazat/<int:pk>/bonus",
        views.DeleteBonusView.as_view(),
        name="delete_bonus",
    ),
]
