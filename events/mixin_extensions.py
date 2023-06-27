from django.contrib import messages


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
