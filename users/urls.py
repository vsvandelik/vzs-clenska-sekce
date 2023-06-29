from django.urls import path
from django.contrib import auth

from . import views

app_name = "users"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("pridat/", views.UserCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/smazat/", views.UserDeleteView.as_view(), name="delete"),
    path("<int:pk>/upravit/", views.UserEditView.as_view(), name="edit"),
    path("prihlasit/", views.LoginView.as_view(), name="login"),
    path("odhlasit/", auth.views.LogoutView.as_view(), name="logout"),
    path("povoleni/", views.PermissionsView.as_view(), name="permissions"),
    path(
        "povoleni/<int:pk>/",
        views.PermissionDetailView.as_view(),
        name="permission_detail",
    ),
    path(
        "zmenit-aktivni-osobu/",
        views.ChangeActivePersonView.as_view(),
        name="change-active-person",
    ),
    path("google/login", views.GoogleLoginView.as_view(), name="google-login"),
    path("google/auth", views.GoogleAuthView.as_view(), name="google-auth"),
]
