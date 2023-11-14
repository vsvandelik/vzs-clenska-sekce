def active_person(request):
    """
    Injects the active person from the request into the template context.

    Template context variable name is ``active_person``.
    """

    active_person = request.active_person if hasattr(request, "active_person") else None

    return {
        "active_person": active_person,
    }


def logout_remember(request):
    """
    Injects the ``logout_remember`` variable from the request into the template context.

    Template context variable name is ``logout_remember``.
    """

    logout_remember = getattr(request, "logout_remember", False)

    return {
        "logout_remember": logout_remember,
    }
