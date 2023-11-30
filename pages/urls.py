from django.urls import path

from .views import HomeView, PageDetailView, PageEditView

app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("<slug:slug>/", PageDetailView.as_view(), name="detail"),
    path("<slug:slug>/upravit", PageEditView.as_view(), name="edit"),
]
