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
from django.contrib import admin
from django.urls import path, include

from persons import urls as persons_urls
from events import urls as events_urls

urlpatterns = [
    path("osoby/", include("persons.urls")),
    path("admin/", admin.site.urls),
    path("udalosti/", include("events.urls")),
    path(
        "pozice/",
        include((events_urls.positions_urls, "positions"), namespace="positions"),
    ),
    path("uzivatele/", include("users.urls")),
    path(
        "kvalifikace/",
        include(
            (persons_urls.feature_urls, "qualifications"),
            namespace="qualifications",
        ),
        {"feature_type": "qualifications"},
    ),
    path(
        "opravneni/",
        include(
            (persons_urls.feature_urls, "permissions"),
            namespace="permissions",
        ),
        {"feature_type": "permissions"},
    ),
    path(
        "vybaveni/",
        include(
            (persons_urls.feature_urls, "equipments"),
            namespace="equipments",
        ),
        {"feature_type": "equipments"},
    ),
]
