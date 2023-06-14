from django.urls import path, include

from . import views

app_name = "persons"

feature_urls = [
    path("", views.FeatureIndex.as_view(), name="index"),
    path("pridat", views.FeatureEdit.as_view(), name="add"),
    path("<int:pk>", views.FeatureDetail.as_view(), name="detail"),
    path("<int:pk>/upravit", views.FeatureEdit.as_view(), name="edit"),
    path("<int:pk>/smazat", views.FeatureDelete.as_view(), name="delete"),
]

nested_feature_assigning_urls = [
    path("", views.FeatureAssignEditView.as_view(), name="add"),
    path("<int:pk>", views.FeatureAssignEditView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.FeatureAssignDeleteView.as_view(), name="delete"),
]

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("pridat", views.PersonCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/upravit", views.PersonUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.PersonDeleteView.as_view(), name="delete"),
    path(
        "<int:person>/kvalifikace",
        include((nested_feature_assigning_urls, "qualifications")),
        {"feature_type": "qualifications"},
    ),
    path(
        "<int:person>/opravneni",
        include((nested_feature_assigning_urls, "permissions")),
        {"feature_type": "permissions"},
    ),
    path(
        "<int:person>/vybaveni",
        include((nested_feature_assigning_urls, "equipments")),
        {"feature_type": "equipments"},
    ),
]
