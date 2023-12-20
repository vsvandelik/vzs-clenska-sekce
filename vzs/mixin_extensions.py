from os import error

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import ModelForm, ValidationError


class ErrorMessageMixin:
    """
    Add a failure message on successful form submission.
    """

    error_message: str | None = None

    def form_invalid(self, form):
        response = super().form_invalid(form)

        error_message = self.get_error_message(form.errors)

        if error_message:
            messages.error(self.request, error_message)

        return response

    def get_error_message(self, errors):
        if self.error_message is not None:
            return self.error_message

        return errors


class MessagesMixin(SuccessMessageMixin, ErrorMessageMixin):
    pass


class InsertRequestIntoModelFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class InsertActivePersonIntoModelFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["active_person"] = self.request.active_person
        return kwargs


class RelatedAddOrRemoveFormMixin(ModelForm):
    error_message: str
    instance_to_add_or_remove_field_name: str

    @staticmethod
    def _process_related(instances, instance):
        raise NotImplementedError

    @staticmethod
    def _is_valid_presence(instances, instance_to_add):
        raise NotImplementedError

    def _get_instances(self):
        raise NotImplementedError

    def clean(self):
        cleaned_data = super().clean()

        instances = self._get_instances()
        instance_to_add = cleaned_data[self.instance_to_add_or_remove_field_name]

        if not self._is_valid_presence(instances, instance_to_add):
            raise ValidationError(self.error_message)

        return cleaned_data

    def save(self, commit=True):
        instances = self._get_instances()
        instance_to_add_or_remove = self.cleaned_data[
            self.instance_to_add_or_remove_field_name
        ]

        self._process_related(instances, instance_to_add_or_remove)

        return self.instance


class RelatedAddMixin:
    @staticmethod
    def _process_related(instances, instance):
        instances.add(instance)

    @staticmethod
    def _is_valid_presence(instances, instance_to_add):
        return not instances.contains(instance_to_add)


class RelatedRemoveMixin:
    @staticmethod
    def _process_related(instances, instance):
        instances.remove(instance)

    @staticmethod
    def _is_valid_presence(instances, instance_to_add):
        return instances.contains(instance_to_add)
