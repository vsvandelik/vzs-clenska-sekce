from django.urls import path

from .views import CreateView

urlpatterns = [path("vytvorit/", CreateView.as_view(), name="users-create")]
