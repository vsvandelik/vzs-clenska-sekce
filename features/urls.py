from django.urls import path

from . import views

app_name = "features"

urlpatterns = [
    path("", views.FeatureIndexView.as_view(), name="index"),
    path("pridat/", views.FeatureEditView.as_view(), name="add"),
    path("<int:pk>/", views.FeatureDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit/", views.FeatureEditView.as_view(), name="edit"),
    path("<int:pk>/smazat/", views.FeatureDeleteView.as_view(), name="delete"),
]
