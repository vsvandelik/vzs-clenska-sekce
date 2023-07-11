from tempus_dominus import widgets


class DatePickerWithIcon(widgets.DatePicker):
    def __init__(self, attrs=None, options=None, format=None):
        if not attrs:
            attrs = {}

        if "append" not in attrs:
            attrs["append"] = "fas fa-calendar"

        super().__init__(attrs, options, format)


class DateTimePickerWithIcon(widgets.DateTimePicker):
    def __init__(self, attrs=None, options=None, format=None):
        if not attrs:
            attrs = {}

        if "append" not in attrs:
            attrs["append"] = "fas fa-calendar"

        if not options:
            options = {}

        if "icons" not in options:
            options["icons"] = {"time": "far fa-clock"}

        super().__init__(attrs, options, format)


class TimePickerWithIcon(widgets.TimePicker):
    def __init__(self, attrs=None, options=None, format=None):
        if not attrs:
            attrs = {}

        if "append" not in attrs:
            attrs["append"] = "fas fa-calendar"

        super().__init__(attrs, options, format)
