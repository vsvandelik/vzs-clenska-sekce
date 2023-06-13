from django.shortcuts import redirect
from django.urls import reverse_lazy
from .models import Event
from django.views import generic
from .forms import TrainingForm
from dateutil.parser import parse
import datetime
from django.forms import ValidationError
from .utils import weekday_pretty, day_shortcut_2_weekday, weekday_2_day_shortcut


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["events"] = Event.objects.filter(parent__isnull=True)
        return context


class EventDeleteView(generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = kwargs["object"]
        context["children"] = context["event"].get_children_trainings_sorted()
        return context


class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = kwargs["object"]
        if context["event"].is_top_training():
            context["children"] = context["event"].get_children_trainings_sorted()
            context["is_training"] = True
            weekdays = context["event"].get_weekdays_trainings_occur()
            weekdays = list(map(weekday_pretty, weekdays))
            context["weekdays"] = ", ".join(weekdays)
            context["weekly_occurs"] = len(weekdays)
        return context


class TrainingCreateView(generic.FormView):
    template_name = "events/edit-training.html"
    form_class = TrainingForm
    success_url = reverse_lazy("events:index")

    def _check_date_constraints(self, form):
        d_start = parse(form["starts_date"].data)
        d_end = parse(form["ends_date"].data)
        if d_start + datetime.timedelta(days=14) > d_end:
            raise ValidationError("Pravidelná událost se koná alespoň 2 týdny")

    def _check_training_time_of_chosen_day(self, form, day):
        from_time = form[f"from_{day}"].data
        to_time = form[f"to_{day}"].data
        from_h, from_m = [int(x) for x in from_time.split(":")]
        to_h, to_m = [int(x) for x in to_time.split(":")]
        if not (from_h < to_h or (from_h <= to_h and from_m < to_m)):
            raise ValidationError("Konec tréningu je čas před jeho začátkem")

    def _check_if_training_occurs_on_day_of_week(self, form, d, weekdays):
        if day_shortcut_2_weekday(d) not in weekdays:
            raise ValidationError(
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků"
            )

    def _check_days_chosen_constraints(self, form):
        days = ["po", "ut", "st", "ct", "pa", "so", "ne"]
        days = {d for d in days if form[d].data}
        number_of_chosen_days = len(days)
        trainings_per_week = int(form["trainings_per_week"].data)
        if trainings_per_week == number_of_chosen_days:
            training_dates = [
                datetime.datetime.strptime(x, "%d.%m.%Y") for x in form["day"].data
            ]
            weekdays = {x.weekday() for x in training_dates}
            weekdays_shortcut = {weekday_2_day_shortcut(x) for x in weekdays}
            if days != weekdays_shortcut:
                raise ValidationError(
                    "Konkrétní trénink se musí konat v jenom z určených dnů pro pravidelné opakování"
                )
            for d in days:
                self._check_training_time_of_chosen_day(form, d)
                self._check_if_training_occurs_on_day_of_week(form, d, weekdays)
            d_start = parse(form["starts_date"].data)
            d_end = parse(form["ends_date"].data)
            for td in training_dates:
                if not d_start <= td <= d_end:
                    raise ValidationError(
                        "Konkrétní trénink se musí konat v platném rozmezí pravidelné události"
                    )
        else:
            raise ValidationError(
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků"
            )

    def _check_constraints(self, form):
        self._check_date_constraints(form)
        self._check_days_chosen_constraints(form)

    def form_valid(self, form):
        """
        Executing form_valid actually means that basic constrains captured in the model
        are checked.
        There are additional constraints that must be checked manually
        """
        try:
            self._check_constraints(form)
        except ValidationError as e:
            raise e
        form.save()
        return redirect("events:index")

    def form_invalid(self, form):
        return redirect("events:index")
