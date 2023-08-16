from django.urls import path
from . import views

app_name = "one_time_events"

urlpatterns = [
    path(
        "<int:pk>/",
        views.OneTimeEventDetailView.as_view(),
        name="detail",
    ),
    path("pridat/", views.OneTimeEventCreateView.as_view(), name="add"),
    path(
        "<int:pk>/upravit/",
        views.OneTimeEventUpdateView.as_view(),
        name="edit",
    ),
]
