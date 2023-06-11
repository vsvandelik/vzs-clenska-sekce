from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("novy-trenink/", views.new_training, name="create_training"),
    path("nova-jednorazova/", views.new_one_time_event, name="new_one_time_event"),
    path("detail/<int:event_id>", views.detail, name="detail"),
]
