from django.urls import path

from .views import (
    ChangeActivePersonView,
    GoogleAuthView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    PermissionDetailView,
    PermissionsView,
    UserResetPasswordRequestView,
    UserResetPasswordView,
)

app_name = "users"

urlpatterns = [
    path("prihlasit/", LoginView.as_view(), name="login"),
    path("odhlasit/", LogoutView.as_view(), name="logout"),
    path(
        "resetovat-heslo/",
        UserResetPasswordRequestView.as_view(),
        name="reset-password-request",
    ),
    path(
        "obnova-zapomenuteho-hesla/",
        UserResetPasswordView.as_view(),
        name="reset-password",
    ),
    path("povoleni/", PermissionsView.as_view(), name="permissions"),
    path(
        "povoleni/<int:pk>/",
        PermissionDetailView.as_view(),
        name="permission_detail",
    ),
    path(
        "zmenit-aktivni-osobu/",
        ChangeActivePersonView.as_view(),
        name="change-active-person",
    ),
    path("google/login/", GoogleLoginView.as_view(), name="google-login"),
    path("google/auth/", GoogleAuthView.as_view(), name="google-auth"),
]
