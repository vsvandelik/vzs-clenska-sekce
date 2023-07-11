from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("<slug:slug>/", views.PageDetailView.as_view(), name="detail"),
    path("<slug:slug>/upravit", views.PageEditView.as_view(), name="edit"),
]
