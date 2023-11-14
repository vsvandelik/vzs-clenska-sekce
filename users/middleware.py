from persons.models import Person


class ActivePersonMiddleware:
    """
    Injects the active person from the session into the request object.

    Request member variable name: ``active_person``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_person_pk = request.session.get("_active_person_pk", None)

        request.active_person = (
            Person.objects.get(pk=active_person_pk)
            if active_person_pk is not None
            else None
        )

        response = self.get_response(request)

        return response


class LogoutRememberMiddleware:
    """
    Injects the ``logout_remember`` variable from cookies into the request object.

    Request member variable name: ``logout_remember``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logout_remember = "logout_remember" in request.COOKIES

        request.logout_remember = logout_remember

        response = self.get_response(request)

        return response
