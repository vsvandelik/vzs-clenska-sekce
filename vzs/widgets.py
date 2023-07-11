from tempus_dominus import widgets


class DatePickerWithIcon(widgets.DatePicker):
    def __init__(self, attrs=None, options=None, format=None):
        attrs = attrs or {}
        attrs.setdefault("append", "fas fa-calendar")

        super().__init__(attrs, options, format)


class DateTimePickerWithIcon(widgets.DateTimePicker):
    def __init__(self, attrs=None, options=None, format=None):
        attrs = attrs or {}
        attrs.setdefault("append", "fas fa-calendar")

        options = options or {}
        options.setdefault("icons", {"time": "far fa-clock"})

        super().__init__(attrs, options, format)


class TimePickerWithIcon(widgets.TimePicker):
    def __init__(self, attrs=None, options=None, format=None):
        attrs = attrs or {}
        attrs.setdefault("append", "far fa-clock")

        super().__init__(attrs, options, format)
