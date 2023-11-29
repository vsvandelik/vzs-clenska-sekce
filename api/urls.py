from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TokenDeleteView, TokenGenerateView, TokenIndexView
from .viewsets import (
    FeatureViewSet,
    GroupViewSet,
    OneTimeEventViewSet,
    PersonExistsView,
    PersonViewSet,
    PositionViewSet,
    TrainingViewSet,
    TransactionViewSet,
    UserViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register("osoby", PersonViewSet)
router.register("vlastnosti", FeatureViewSet)
router.register("skupiny", GroupViewSet)
router.register("jednorazove", OneTimeEventViewSet)
router.register("treninky", TrainingViewSet)
router.register("pozice", PositionViewSet)
router.register("transakce", TransactionViewSet)
router.register("uzivatele", UserViewSet)


token_urlpatterns = [
    path(
        "",
        TokenIndexView.as_view(),
        name="index",
    ),
    path(
        "<str:pk>/smazat/",
        TokenDeleteView.as_view(),
        name="delete",
    ),
    path(
        "generovat/",
        TokenGenerateView.as_view(),
        name="generate",
    ),
]

urlpatterns = [
    path("osoby/existuje/", PersonExistsView.as_view()),
    path("", include(router.urls)),
    path("tokeny/", include((token_urlpatterns, "token"), namespace="token")),
]
