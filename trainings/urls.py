from django.urls import path

from . import views

app_name = "trainings"

urlpatterns = [
    path("<int:pk>/", views.TrainingDetailView.as_view(), name="detail"),
    path("pridat/", views.TrainingCreateView.as_view(), name="add"),
    path(
        "<int:pk>/upravit/",
        views.TrainingUpdateView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/pridat-nahradu/",
        views.TrainingAddReplaceableTrainingView.as_view(),
        name="add-replaceable-training",
    ),
    path(
        "<int:pk>/odebrat-nahradu/",
        views.TrainingRemoveReplaceableTrainingView.as_view(),
        name="remove-replaceable-training",
    ),
]
