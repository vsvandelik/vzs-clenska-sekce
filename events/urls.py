from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventIndexView.as_view(), name="index"),
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.EventDetailView.as_view(), name="detail"),
    path("pridat-trenink/", views.TrainingCreateView.as_view(), name="add_training"),
    path(
        "pridat-jednorazovou/",
        views.OneTimeEventCreateView.as_view(),
        name="add_one_time_event",
    ),
    path(
        "<int:pk>/upravit-jednorazovou/",
        views.OneTimeEventUpdateView.as_view(),
        name="edit_one_time_event",
    ),
    path(
        "<int:pk>/upravit-trenink/",
        views.TrainingUpdateView.as_view(),
        name="edit_training",
    ),
]
