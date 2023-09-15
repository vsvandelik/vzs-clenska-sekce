from django.contrib.auth.backends import ModelBackend
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model

from vzs import settings
from persons.models import Person


UserModel = get_user_model()


class PasswordBackend(ModelBackend):
    def authenticate(self, request, email, password, **kwargs):
        person = Person.objects.filter(email=email).first()
        return super().authenticate(request, person=person, password=password, **kwargs)


class GoogleBackend(ModelBackend):
    _flow = Flow.from_client_secrets_file(
        settings.GOOGLE_SECRETS_FILE,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
    )

    @classmethod
    def _state_encode(cls, state):
        return "x" + state

    @classmethod
    def state_decode(cls, state):
        return state[1:]

    @classmethod
    def get_redirect_url(cls, request, view_name, next_redirect):
        cls._flow.redirect_uri = request.build_absolute_uri(reverse(view_name))

        url, _ = cls._flow.authorization_url(
            prompt="consent", state=cls._state_encode(next_redirect)
        )

        return url

    def authenticate(self, request, code, **kwargs):
        if code is None:
            return

        self._flow.fetch_token(code=code)
        token = id_token.verify_oauth2_token(self._flow.credentials.id_token, Request())

        if "email" not in token:
            return

        email = token["email"]

        person = Person.objects.get(email=email)

        user = UserModel._default_manager.get_by_natural_key(person)

        if not self.user_can_authenticate(user):
            return

        return user
