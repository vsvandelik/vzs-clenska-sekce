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

urlpatterns = [
    path("", include(router.urls)),
]
