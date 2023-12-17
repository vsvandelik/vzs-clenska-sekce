from django.urls import path

from .views import (
    FeatureAssignToSelectedPersonView,
    FeatureDeleteView,
    FeatureDetailView,
    FeatureEditView,
    FeatureIndexView,
)

app_name = "features"

urlpatterns = [
    path("", FeatureIndexView.as_view(), name="index"),
    path("pridat/", FeatureEditView.as_view(), name="add"),
    path("<int:pk>/", FeatureDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit/", FeatureEditView.as_view(), name="edit"),
    path("<int:pk>/smazat/", FeatureDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/pridelit/",
        FeatureAssignToSelectedPersonView.as_view(),
        name="assign",
    ),
]
