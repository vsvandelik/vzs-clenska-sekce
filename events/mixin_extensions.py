from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from .models import Event


class FailureMessageMixin:
    """
    Add a failure message on successful form submission.
    """

    def form_invalid(self, form):
        response = super().form_invalid(form)
        failure_message = self.get_failure_message(form.errors)
        if failure_message:
            messages.error(self.request, failure_message)
        return response

    def get_failure_message(self, errors):
        return errors


class MessagesMixin(SuccessMessageMixin, FailureMessageMixin):
    pass


class InvariantMixin:
    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        event.set_type()
        if not self.invariant(event):
            return redirect(self.invariant_failed_redirect_url)
        return super().get(request, *args, **kwargs)
