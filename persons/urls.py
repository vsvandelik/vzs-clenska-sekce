from django.urls import path

from . import views

app_name = 'persons'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('pridat', views.PersonCreateView.as_view(), name='add'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/upravit', views.PersonUpdateView.as_view(), name='edit'),
    path('<int:pk>/smazat', views.PersonDeleteView.as_view(), name='delete'),
]
