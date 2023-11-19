from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.urls import reverse
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from persons.models import Person
from vzs import settings

UserModel = get_user_model()


class PasswordBackend(ModelBackend):
    """
    Authentication with an email address instead of the default username.
    """

    def authenticate(self, request, email, password, **kwargs):
        """
        Authenticates with an email address and password.
        """

        person = Person.objects.filter(email=email).first()
        return super().authenticate(request, person=person, password=password, **kwargs)


class GoogleBackend(ModelBackend):
    """
    Authentication through Google OAuth2.
    """

    _flow = Flow.from_client_secrets_file(
        settings.GOOGLE_SECRETS_FILE,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
    )

    @classmethod
    def _state_encode(cls, state):
        return "x" + state

    @classmethod
    def state_decode(cls, state):
        """
        Decodes the state query parameter received from Google.

        Returns the redirect URL passed to :func:`create_redirect_url`.
        """

        return state[1:]

    @classmethod
    def create_redirect_url(cls, request, view_name, next_redirect):
        """
        Creates the URL to redirect to for Google authentication.

        After a successful authentication, Google will send a HTTP GET request
        to ``view_name`` with query parameters ``code`` and ``state``.
        The ``state`` parameter will contain an encoded ``next_redirect``
        (see :func:`state_decode`).

        :parameter request: The request object of the redirecting (login) view.

        :parameter view_name: The pattern of the view for Google to send
            the HTTP GET request with code and state to.

        :parameter next_redirect: The URL to redirect to after a successful
            Google authentication.
        """

        cls._flow.redirect_uri = request.build_absolute_uri(reverse(view_name))

        url, _ = cls._flow.authorization_url(
            prompt="consent", state=cls._state_encode(next_redirect)
        )

        return url

    def authenticate(self, request, code, **kwargs):
        """
        Authenticates with code received from the OAuth server.
        """

        if code is None:
            return None

        self._flow.fetch_token(code=code)
        token = id_token.verify_oauth2_token(self._flow.credentials.id_token, Request())

        if "email" not in token:
            return None

        email = token["email"]

        person = Person.objects.get(email=email)

        user = UserModel._default_manager.get_by_natural_key(person)

        if not self.user_can_authenticate(user):
            return None

        return user
