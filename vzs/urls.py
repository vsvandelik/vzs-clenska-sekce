"""
URL configuration for vzs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

import persons.urls
from pages import views as pages_views

urlpatterns = [
    path(
        "muj-profil/",
        include((persons.urls.my_profile_urlpatterns, "my-profile"), "my-profile"),
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
