from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("pridat/", views.UserCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/smazat", views.UserDeleteView.as_view(), name="delete"),
]
