from django.urls import path, include

from . import views

nested_feature_assigning_urls = [
    path(
        "",
        views.FeatureAssignEditView.as_view(),
        name="add",
    ),
    path(
        "<int:pk>",
        views.FeatureAssignEditView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/smazat",
        views.FeatureAssignDeleteView.as_view(),
        name="delete",
    ),
]

app_name = "persons"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("pridat", views.PersonCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/upravit", views.PersonUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.PersonDeleteView.as_view(), name="delete"),
    path(
        "<int:person>/kvalifikace",
        include(
            (nested_feature_assigning_urls, "qualifications"),
            namespace="qualifications",
        ),
        {"feature_type": "qualifications"},
    ),
    path(
        "<int:person>/opravneni",
        include(
            (nested_feature_assigning_urls, "permissions"), namespace="permissions"
        ),
        {"feature_type": "permissions"},
    ),
    path(
        "<int:person>/vybaveni",
        include((nested_feature_assigning_urls, "equipments"), namespace="equipments"),
        {"feature_type": "equipments"},
    ),
]
