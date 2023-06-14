from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("pridat/", views.UserCreateView.as_view(), name="add"),
    path("<int:pk>/smazat", views.UserDeleteView.as_view(), name="delete"),
]
