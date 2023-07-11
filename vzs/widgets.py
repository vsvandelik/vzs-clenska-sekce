from tempus_dominus import widgets

from vzs import settings


class DateTimePickerMixin:
    def _set_locale(self, options, format):
        options = options or {}
        options.setdefault("locale", "cs")
        options.setdefault("format", format)
        return options

    def _set_calendar_icon(self, attrs):
        attrs = attrs or {}
        attrs.setdefault("append", "fas fa-calendar")
        return attrs


class DatePickerWithIcon(widgets.DatePicker, DateTimePickerMixin):
    def __init__(self, attrs=None, options=None, format=None):
        attrs = self._set_calendar_icon(attrs)
        options = self._set_locale(options, settings.TEMPUS_DOMINUS_DATE_FORMAT)

        super().__init__(attrs, options, format)


class DateTimePickerWithIcon(widgets.DateTimePicker, DateTimePickerMixin):
    def __init__(self, attrs=None, options=None, format=None):
        attrs = self._set_calendar_icon(attrs)
        options = self._set_locale(options, settings.TEMPUS_DOMINUS_DATETIME_FORMAT)
        options.setdefault("icons", {"time": "far fa-clock"})

        super().__init__(attrs, options, format)


class TimePickerWithIcon(widgets.TimePicker, DateTimePickerMixin):
    def __init__(self, attrs=None, options=None, format=None):
        options = self._set_locale(options, settings.TEMPUS_DOMINUS_TIME_FORMAT)
        attrs = attrs or {}
        attrs.setdefault("append", "far fa-clock")

        super().__init__(attrs, options, format)
