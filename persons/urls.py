from django.urls import path, include

from . import views

app_name = "persons"

feature_urls = [
    path("", views.FeatureIndexView.as_view(), name="index"),
    path("pridat", views.FeatureEditView.as_view(), name="add"),
    path("<int:pk>", views.FeatureDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit", views.FeatureEditView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.FeatureDeleteView.as_view(), name="delete"),
]

nested_feature_assigning_urls = [
    path("", views.FeatureAssignEditView.as_view(), name="add"),
    path("<int:pk>", views.FeatureAssignEditView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.FeatureAssignDeleteView.as_view(), name="delete"),
]

groups_urlpatterns = [
    path("", views.GroupIndexView.as_view(), name="index"),
    path("<int:pk>/", views.StaticGroupDetailView.as_view(), name="detail"),
    path("pridat/staticka", views.StaticGroupEditView.as_view(), name="add-static"),
    path(
        "<int:pk>/upravit/staticka",
        views.StaticGroupEditView.as_view(),
        name="edit-static",
    ),
    path(
        "<int:group>/odebrat-clena/<int:person>",
        views.StaticGroupRemoveMemberView.as_view(),
        name="remove-member",
    ),
    path("<int:pk>/smazat", views.GroupDeleteView.as_view(), name="delete"),
]

urlpatterns = [
    path("", views.PersonIndexView.as_view(), name="index"),
    path(
        "poslat-email", views.SendEmailToSelectedPersonsView.as_view(), name="send-mail"
    ),
    path("exportovat", views.ExportSelectedPersonsView.as_view(), name="export"),
    path("pridat", views.PersonCreateView.as_view(), name="add"),
    path("<int:pk>/", views.PersonDetailView.as_view(), name="detail"),
    path("<int:pk>/upravit", views.PersonUpdateView.as_view(), name="edit"),
    path("<int:pk>/smazat", views.PersonDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/pridat-spravovanou-osobu",
        views.AddManagedPersonView.as_view(),
        name="add-managed-person",
    ),
    path(
        "<int:pk>/odebrat-spravovanou-osobu",
        views.DeleteManagedPersonView.as_view(),
        name="remove-managed-person",
    ),
    path(
        "<int:person>/kvalifikace/",
        include((nested_feature_assigning_urls, "qualifications")),
        {"feature_type": "qualifications"},
    ),
    path(
        "<int:person>/opravneni/",
        include((nested_feature_assigning_urls, "permissions")),
        {"feature_type": "permissions"},
    ),
    path(
        "<int:person>/vybaveni/",
        include((nested_feature_assigning_urls, "equipments")),
        {"feature_type": "equipments"},
    ),
    path("skupiny/", include((groups_urlpatterns, "groups"))),
]
