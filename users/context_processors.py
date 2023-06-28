def active_person(request):
    active_person = request.active_person if hasattr(request, "active_person") else None

    return {
        "active_person": active_person,
    }
