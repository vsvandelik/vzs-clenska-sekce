def weekday_2_day_shortcut(weekday):
    if weekday == 0:
        return "po"
    elif weekday == 1:
        return "ut"
    elif weekday == 2:
        return "st"
    elif weekday == 3:
        return "ct"
    elif weekday == 4:
        return "pa"
    elif weekday == 5:
        return "so"
    return "ne"


def day_shortcut_2_weekday(day_shortcut):
    if day_shortcut == "po":
        return 0
    elif day_shortcut == "ut":
        return 1
    elif day_shortcut == "st":
        return 2
    elif day_shortcut == "ct":
        return 3
    elif day_shortcut == "pa":
        return 4
    elif day_shortcut == "so":
        return 5
    return 6


def weekday_pretty(weekday):
    if weekday == 0:
        return "Po"
    elif weekday == 1:
        return "Út"
    elif weekday == 2:
        return "St"
    elif weekday == 3:
        return "Čt"
    elif weekday == 4:
        return "Pá"
    elif weekday == 5:
        return "So"
    return "Ne"


def days_shortcut_list():
    return ["po", "ut", "st", "ct", "pa", "so", "ne"]


def days_pretty_list():
    return ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
