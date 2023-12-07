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
router.register("persons", PersonViewSet)
router.register("features", FeatureViewSet)
router.register("groups", GroupViewSet)
router.register("one-time", OneTimeEventViewSet)
router.register("trainings", TrainingViewSet)
router.register("positions", PositionViewSet)
router.register("transactions", TransactionViewSet)
router.register("users", UserViewSet)


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
    path("persons/exists/", PersonExistsView.as_view()),
    path("", include(router.urls)),
    path("tokeny/", include((token_urlpatterns, "token"), namespace="token")),
]
