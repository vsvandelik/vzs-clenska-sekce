from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventIndexView.as_view(), name="index"),
    path("<int:pk>/smazat/", views.EventDeleteView.as_view(), name="delete"),
    path("<int:pk>/detail/", views.EventDetailView.as_view(), name="detail"),
    path("novy-trenink/", views.TrainingCreateView.as_view(), name="create_training"),
]
