from .viewsets import (
    PersonViewSet,
    FeatureViewSet,
    GroupViewSet,
    OneTimeEventViewSet,
    TrainingViewSet,
    PositionViewSet,
    TransactionViewSet,
    UserViewSet,
)
from .views import TokenGenerateView, TokenIndexView, TokenDeleteView

from rest_framework.routers import DefaultRouter

from django.urls import path, include


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
    path("", include(router.urls)),
    path("tokeny/", include((token_urlpatterns, "token"), namespace="token")),
]
