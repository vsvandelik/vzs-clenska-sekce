from django.urls import path

from . import views

app_name = "users"
urlpatterns = [path("pridat/", views.UserCreateView.as_view(), name="add")]
