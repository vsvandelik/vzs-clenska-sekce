from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "users"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("pridat/", views.UserCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/smazat/", views.UserDeleteView.as_view(), name="delete"),
    path("<int:pk>/upravit/", views.UserEditView.as_view(), name="edit"),
    path("prihlasit/", views.LoginView.as_view(), name="login"),
    path("odhlasit/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "zmenit-aktivni-osobu/",
        views.ChangeActivePersonView.as_view(),
        name="change-active-person",
    ),
]
