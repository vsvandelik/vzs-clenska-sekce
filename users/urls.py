from django.contrib import auth
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("prihlasit/", views.LoginView.as_view(), name="login"),
    path("odhlasit/", auth.views.LogoutView.as_view(), name="logout"),
    path(
        "resetovat-heslo-zadost/",
        views.UserResetPasswordRequestView.as_view(),
        name="reset-password-request",
    ),
    path(
        "resetovat-heslo/",
        views.UserResetPasswordView.as_view(),
        name="reset-password",
    ),
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
    path("google/login/", views.GoogleLoginView.as_view(), name="google-login"),
    path("google/auth/", views.GoogleAuthView.as_view(), name="google-auth"),
]
