from django.urls import include, path

import persons.urls
import transactions.views
from pages import views as pages_views

urlpatterns = [
    path(
        "muj-profil/",
        include((persons.urls.my_profile_urlpatterns, "my-profile"), "my-profile"),
    ),
    path(
        "moje-transakce/",
        transactions.views.MyTransactionsView.as_view(),
        name="my-transactions",
    ),
    path("osoby/", include("persons.urls")),
    path("transakce/", include("transactions.urls")),
    path("udalosti/", include("events.urls")),
    path("udalosti/jednorazove/", include("one_time_events.urls")),
    path("udalosti/treninky/", include("trainings.urls")),
    path("pozice/", include("positions.urls")),
    path("uzivatele/", include("users.urls")),
    path("skupiny/", include("groups.urls")),
    path(
        "kvalifikace/",
        include("features.urls", namespace="qualifications"),
        {"feature_type": "qualifications"},
    ),
    path(
        "opravneni/",
        include("features.urls", namespace="permissions"),
        {"feature_type": "permissions"},
    ),
    path(
        "vybaveni/",
        include("features.urls", namespace="equipments"),
        {"feature_type": "equipments"},
    ),
    path("tinymce/", include("tinymce.urls")),
    path("select2/", include("django_select2.urls")),
    path("api/", include("api.urls")),
    path("", include("pages.urls")),
]

handler400 = pages_views.ErrorPage400View.as_view()
handler403 = pages_views.ErrorPage403View.as_view()
handler404 = pages_views.ErrorPage404View.as_view()
handler500 = pages_views.ErrorPage500View.as_view()
