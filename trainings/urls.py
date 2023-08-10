from django.urls import path
from . import views

app_name = "trainings"

urlpatterns = [
    path(
        "<int:pk>/trenink/", views.TrainingDetailView.as_view(), name="detail_training"
    ),
    path("pridat/trenink/", views.TrainingCreateView.as_view(), name="add_training"),
    path(
        "<int:pk>/upravit/trenink/",
        views.TrainingUpdateView.as_view(),
        name="edit_training",
    ),
]
