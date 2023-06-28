from django.urls import path
from django.contrib import auth

from . import views

app_name = "users"

urlpatterns = [
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
]
