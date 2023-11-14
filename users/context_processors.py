def active_person(request):
    active_person = request.active_person if hasattr(request, "active_person") else None

    return {
        "active_person": active_person,
    }


def logout_remember(request):
    logout_remember = getattr(request, "logout_remember", False)

    return {
        "logout_remember": logout_remember,
    }
