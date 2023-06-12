from django.urls import path

from . import views

qualifications_urls = [
    path("", views.QualificationIndex.as_view(), name="index"),
    path("pridat", views.QualificationEdit.as_view(), name="add"),
    path("<int:pk>", views.QualificationDetail.as_view(), name="detail"),
    path("<int:pk>/upravit", views.QualificationEdit.as_view(), name="edit"),
    path("<int:pk>/smazat", views.QualificationDelete.as_view(), name="delete"),
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
        views.QualificationAssignAddView.as_view(),
        name="qualification-add",
    ),
    path(
        "<int:person>/kvalifikace/<int:pk>",
        views.QualificationAssignEditView.as_view(),
        name="qualification-edit",
    ),
    path(
        "<int:person>/kvalifikace/<int:pk>/smazat",
        views.QualificationAssignDeleteView.as_view(),
        name="qualification-delete",
    ),
    path(
        "<int:person>/opravneni",
        views.PermissionAssignAddView.as_view(),
        name="permission-add",
    ),
    path(
        "<int:person>/opravneni/<int:pk>",
        views.PermissionAssignEditView.as_view(),
        name="permission-edit",
    ),
    path(
        "<int:person>/opravneni/<int:pk>/smazat",
        views.PermissionAssignDeleteView.as_view(),
        name="permission-delete",
    ),
    path(
        "<int:person>/vybaveni",
        views.EquipmentAssignAddView.as_view(),
        name="equipment-add",
    ),
    path(
        "<int:person>/vybaveni/<int:pk>",
        views.EquipmentAssignEditView.as_view(),
        name="equipment-edit",
    ),
    path(
        "<int:person>/vybaveni/<int:pk>/smazat",
        views.EquipmentAssignDeleteView.as_view(),
        name="equipment-delete",
    ),
]
